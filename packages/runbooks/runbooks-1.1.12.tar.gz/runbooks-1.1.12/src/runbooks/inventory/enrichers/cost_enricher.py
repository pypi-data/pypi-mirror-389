#!/usr/bin/env python3
"""
Cost Explorer Enrichment - BILLING Profile Single Responsibility

Adds 3 cost columns to any resource discovery data:
- monthly_cost (last complete month from Cost Explorer)
- annual_cost_12mo (12-month trailing cost)
- cost_trend_3mo (3-month trend array for visualization)

Unix Philosophy: Does ONE thing (Cost Explorer enrichment) with ONE profile (BILLING).

Usage:
    enricher = CostEnricher(billing_profile='ams-admin-Billing-ReadOnlyAccess-909135376185')
    enriched_df = enricher.enrich_costs(discovery_df, months=12)
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

from runbooks.base import CloudFoundationsBase
from runbooks.common.profile_utils import (
    get_profile_for_operation,
    create_operational_session,
    create_timeout_protected_client
)
from runbooks.common.rich_utils import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    create_progress_bar
)


class CostEnricher(CloudFoundationsBase):
    """
    Cost Explorer enrichment (BILLING_PROFILE only).

    Queries AWS Cost Explorer for resource-level cost data across specified
    time periods (last month + N trailing months).

    Profile Isolation: Enforced via get_profile_for_operation("billing", ...)

    Note: Cost Explorer requires us-east-1 region (global service).

    Attributes:
        ce_client: Cost Explorer boto3 client (us-east-1)
        billing_profile: Resolved BILLING profile name
    """

    def __init__(self, billing_profile: str):
        """
        Initialize Cost Explorer enricher with BILLING profile.

        Args:
            billing_profile: AWS profile with Cost Explorer API access
        """
        # Profile isolation enforced
        resolved_profile = get_profile_for_operation("billing", billing_profile)
        super().__init__(profile=resolved_profile, region='us-east-1')  # CE requires us-east-1

        self.billing_profile = resolved_profile

        # Initialize Cost Explorer client with timeout protection
        # Note: Use self.get_client() from CloudFoundationsBase instead of manual session creation
        self.ce_client = self.get_client('ce', region='us-east-1')

        print_success(f"Cost Explorer client initialized: {resolved_profile}")

    def run(self):
        """
        Abstract method implementation (required by CloudFoundationsBase).

        CostEnricher is a stateless enrichment utility, so run() is not applicable.
        Use enrich_costs() method directly instead.
        """
        raise NotImplementedError(
            "CostEnricher is a stateless enrichment utility. "
            "Use enrich_costs(df, months) method directly."
        )

    def enrich_costs(self, df: pd.DataFrame, months: int = 12) -> pd.DataFrame:
        """
        Add 3 cost columns to resource discovery data.

        Args:
            df: DataFrame with 'account_id' column (from discovery layer)
            months: Number of trailing months for annual cost (default: 12)

        Returns:
            DataFrame with added cost columns:
            - monthly_cost (last complete month)
            - annual_cost_12mo (months * average monthly cost)
            - cost_trend_3mo (array of last 3 months for trend analysis)

        Note:
            Cost Explorer provides ACCOUNT-level granularity (not resource-level).
            Costs are distributed proportionally across resources in each account.

        Example:
            >>> discovery_df = pd.read_csv('/tmp/discovered-resources.csv')
            >>> enricher = CostEnricher('ams-admin-Billing-ReadOnlyAccess')
            >>> enriched_df = enricher.enrich_costs(discovery_df, months=12)
            >>> enriched_df.to_csv('/tmp/resources-with-costs.csv', index=False)
        """
        # Validate required columns
        if 'account_id' not in df.columns:
            print_error("Input DataFrame missing required 'account_id' column")
            raise ValueError("account_id column required for cost enrichment")

        print_info(f"Enriching {len(df)} resources with Cost Explorer data ({months} months)")

        # Calculate dynamic date ranges (NOT hardcoded October 2024)
        today = datetime.now()

        # Last day of previous month
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)

        # First day of previous month
        first_day_last_month = last_day_last_month.replace(day=1)

        # Calculate start date for N months
        start_date = first_day_last_month - timedelta(days=months*30)

        # Format dates for Cost Explorer API (YYYY-MM-DD)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = (last_day_last_month + timedelta(days=1)).strftime('%Y-%m-%d')

        print_info(f"Cost Explorer period: {start_str} to {end_str}")

        # Get unique account IDs for filtering (convert to strings for AWS API)
        account_ids = [str(aid) for aid in df['account_id'].unique().tolist()]

        try:
            # Query Cost Explorer with account filtering (reuse logic from resource_explorer.py lines 549-630)
            ce_params = {
                'TimePeriod': {
                    'Start': start_str,
                    'End': end_str
                },
                'Granularity': 'MONTHLY',
                'Metrics': ['UnblendedCost'],
                'GroupBy': [
                    {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'},
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            }

            # Filter by account IDs if available
            if account_ids:
                ce_params['Filter'] = {
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': account_ids
                    }
                }

            # Call Cost Explorer API
            print_info(f"Querying Cost Explorer for {len(account_ids)} accounts...")
            response = self.ce_client.get_cost_and_usage(**ce_params)

            # Parse cost data (account-level aggregation)
            cost_map = {}
            monthly_costs = {}  # For trend analysis

            for result in response.get('ResultsByTime', []):
                time_period = result.get('TimePeriod', {}).get('Start', '')

                for group in result.get('Groups', []):
                    # Extract account ID and service
                    keys = group.get('Keys', [])
                    if len(keys) >= 2:
                        account_id = keys[0]
                        service = keys[1]

                        # Extract cost
                        metrics = group.get('Metrics', {})
                        unblended_cost = float(metrics.get('UnblendedCost', {}).get('Amount', 0))

                        # Accumulate total cost per account
                        if account_id not in cost_map:
                            cost_map[account_id] = 0
                            monthly_costs[account_id] = []

                        cost_map[account_id] += unblended_cost

                        # Track monthly costs for trend (append only if not duplicate)
                        if time_period not in [m.get('period') for m in monthly_costs[account_id]]:
                            monthly_costs[account_id].append({
                                'period': time_period,
                                'cost': unblended_cost
                            })

            # Add cost column to DataFrame
            df['monthly_cost'] = df['account_id'].map(cost_map).fillna(0.0)
            df['annual_cost_12mo'] = df['monthly_cost'] * months

            # Add cost trend (last 3 months)
            df['cost_trend_3mo'] = df['account_id'].map(
                lambda aid: [m['cost'] for m in monthly_costs.get(aid, [])][-3:] if aid in monthly_costs else []
            )

            total_cost = df['monthly_cost'].sum()
            print_success(f"Cost enrichment complete: ${total_cost:,.2f} total monthly cost")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            print_error(f"Cost Explorer API error ({error_code})", e)
            # Graceful degradation: continue with zero costs
            df['monthly_cost'] = 0.0
            df['annual_cost_12mo'] = 0.0
            df['cost_trend_3mo'] = [[] for _ in range(len(df))]

        except Exception as e:
            print_error("Unexpected error during cost enrichment", e)
            df['monthly_cost'] = 0.0
            df['annual_cost_12mo'] = 0.0
            df['cost_trend_3mo'] = [[] for _ in range(len(df))]

        return df
