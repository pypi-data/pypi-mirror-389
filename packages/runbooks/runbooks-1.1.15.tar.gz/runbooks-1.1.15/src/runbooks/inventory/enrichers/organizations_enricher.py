#!/usr/bin/env python3
"""
Organizations Metadata Enrichment - MANAGEMENT Profile Single Responsibility

Adds 10 Organizations columns to any resource discovery data:
- account_name, account_email (from Organizations DescribeAccount)
- account_status, account_join_method, account_join_date (Phase 0 Manager Correction)
- wbs_code, cost_group (TIER 1 business metadata)
- technical_lead, account_owner (TIER 2 governance metadata)
- organizational_unit (from Organizations ListParents)

Unix Philosophy: Does ONE thing (Organizations enrichment) with ONE profile (MANAGEMENT).

Usage:
    enricher = OrganizationsEnricher(management_profile='ams-admin-ReadOnlyAccess-909135376185')
    enriched_df = enricher.enrich_dataframe(discovery_df)
"""

import pandas as pd
from typing import Dict, List, Optional

from runbooks.base import CloudFoundationsBase
from runbooks.common.profile_utils import get_profile_for_operation
from runbooks.common.rich_utils import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    create_progress_bar
)
from runbooks.inventory.organizations_utils import discover_organization_accounts


class OrganizationsEnricher(CloudFoundationsBase):
    """
    Organizations metadata enrichment (MANAGEMENT_PROFILE only).

    Enriches resource discovery data with 10 Organizations columns by mapping
    account_id to Organizations metadata via discover_organization_accounts().

    Profile Isolation: Enforced via get_profile_for_operation("management", ...)

    Attributes:
        accounts (List[Dict]): Organization accounts with TIER 1-4 metadata
        account_lookup (Dict[str, Dict]): Fast account_id → metadata mapping
        error (Optional[str]): Organizations API error if unavailable
    """

    def __init__(self, management_profile: str, region: str = "ap-southeast-2"):
        """
        Initialize Organizations enricher with MANAGEMENT profile.

        Args:
            management_profile: AWS profile with Organizations API access
            region: AWS region for global services (default: ap-southeast-2)
        """
        # Profile isolation enforced
        resolved_profile = get_profile_for_operation("management", management_profile)
        super().__init__(profile=resolved_profile, region=region)

        self.management_profile = resolved_profile
        self.region = region

        # Discover organization accounts (reuse existing pattern from enrich_ec2.py)
        print_info(f"Discovering accounts via Organizations API (profile: {resolved_profile})")
        self.accounts, self.error = discover_organization_accounts(resolved_profile, region)

        if self.error:
            print_warning(f"Organizations unavailable: {self.error}")
            print_info("Enrichment will use account IDs only (no Organizations metadata)")

        # Create account lookup dict for fast access
        self.account_lookup = {acc['id']: acc for acc in self.accounts}

        print_success(f"Initialized with {len(self.accounts)} accounts")

    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add 10 Organizations columns to resource discovery data.

        Args:
            df: DataFrame with 'account_id' column (from discovery layer)

        Returns:
            DataFrame with added Organizations columns:
            - account_name, account_email
            - account_status, account_join_method, account_join_date (Phase 0 Manager Correction)
            - wbs_code, cost_group
            - technical_lead, account_owner
            - organizational_unit

        Raises:
            ValueError: If input DataFrame missing 'account_id' column

        Example:
            >>> discovery_df = pd.read_csv('/tmp/discovered-resources.csv')
            >>> enricher = OrganizationsEnricher('ams-admin-ReadOnlyAccess')
            >>> enriched_df = enricher.enrich_dataframe(discovery_df)
            >>> enriched_df.to_csv('/tmp/resources-with-orgs.csv', index=False)
        """
        # Validate required columns
        if 'account_id' not in df.columns:
            print_error("Input DataFrame missing required 'account_id' column")
            raise ValueError("account_id column required for Organizations enrichment")

        print_info(f"Enriching {len(df)} resources with Organizations metadata")

        # Initialize 10 Organizations columns (Phase 0 Manager Correction: +3 fields)
        orgs_columns = {
            'account_name': 'N/A',
            'account_email': 'N/A',
            'account_status': 'N/A',           # Phase 0: ACTIVE/SUSPENDED/PENDING_CLOSURE
            'account_join_method': 'N/A',      # Phase 0: INVITED/CREATED/UNKNOWN
            'account_join_date': 'N/A',        # Phase 0: Account creation/join timestamp
            'wbs_code': 'N/A',
            'cost_group': 'N/A',
            'technical_lead': 'N/A',
            'account_owner': 'N/A',
            'organizational_unit': 'N/A'
        }

        for col, default in orgs_columns.items():
            df[col] = default

        # Enrich with actual data (reuse pattern from enrich_ec2.py lines 176-196)
        with create_progress_bar() as progress:
            task = progress.add_task(
                "[cyan]Enriching with Organizations...",
                total=len(df)
            )

            for idx, row in df.iterrows():
                account_id = str(row.get('account_id', '')).strip()

                if account_id in self.account_lookup:
                    acc = self.account_lookup[account_id]
                    df.at[idx, 'account_name'] = acc.get('name', 'N/A')
                    df.at[idx, 'account_email'] = acc.get('email', 'N/A')
                    # Phase 0 Manager Correction: Add 3 new fields
                    df.at[idx, 'account_status'] = acc.get('status', 'N/A')
                    df.at[idx, 'account_join_method'] = acc.get('joined_method', 'N/A')
                    # Format timestamp for readability (ISO format or N/A)
                    join_ts = acc.get('joined_timestamp', 'N/A')
                    df.at[idx, 'account_join_date'] = str(join_ts) if join_ts != 'N/A' else 'N/A'
                    # Existing TIER 1-2 metadata
                    df.at[idx, 'wbs_code'] = acc.get('wbs_code', 'N/A')
                    df.at[idx, 'cost_group'] = acc.get('cost_group', 'N/A')
                    df.at[idx, 'technical_lead'] = acc.get('technical_lead', 'N/A')
                    df.at[idx, 'account_owner'] = acc.get('account_owner', 'N/A')
                    df.at[idx, 'organizational_unit'] = acc.get('organizational_unit', 'N/A')

                progress.update(task, advance=1)

        enriched_count = (df['account_name'] != 'N/A').sum()
        print_success(f"Organizations enrichment complete: {enriched_count}/{len(df)} resources")

        return df

    def run(self):
        """
        Run method required by CloudFoundationsBase.

        For OrganizationsEnricher, this returns initialization status.
        Primary usage is via enrich_dataframe() method.

        Returns:
            CloudFoundationsResult with initialization status
        """
        from runbooks.base import CloudFoundationsResult
        from datetime import datetime

        return CloudFoundationsResult(
            timestamp=datetime.now(),
            success=True,
            message=f"OrganizationsEnricher initialized with {len(self.accounts)} accounts",
            data={
                'account_count': len(self.accounts),
                'management_profile': self.management_profile,
                'region': self.region,
                'organizations_available': self.error is None
            }
        )
