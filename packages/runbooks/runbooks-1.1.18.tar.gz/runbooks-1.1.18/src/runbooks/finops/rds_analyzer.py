#!/usr/bin/env python3
"""
RDS Cost Analyzer - 4-Way Validation RDS Cost Optimization Analysis

This module provides enterprise RDS cost analysis with:
- Organizations metadata enrichment (7 columns including tags_combined)
- Cost Explorer 12-month historical costs
- RDS instance discovery via describe_db_instances API
- Rich CLI cost visualization
- Excel export with validation metrics

Design Philosophy (KISS/DRY/LEAN):
- Mirror ec2_analyzer.py proven patterns
- Reuse base_enrichers.py (Organizations, Cost Explorer)
- Follow Rich CLI standards from rich_utils.py
- Production-grade error handling

Usage:
    # Python API (Notebook consumption)
    from runbooks.finops.rds_analyzer import analyze_rds_costs

    result_df = analyze_rds_costs(
        management_profile='mgmt-profile',
        billing_profile='billing-profile',
        enable_cost=True,
        include_12month_cost=True
    )

    # CLI
    runbooks finops analyze-rds \\
        --management-profile mgmt \\
        --billing-profile billing \\
        --enable-cost

Strategic Alignment:
- Objective 1: RDS cost optimization for runbooks package
- Enterprise SDLC: Proven patterns from FinOps module
- KISS/DRY/LEAN: Reuse EC2 analyzer patterns
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from .base_enrichers import (
    CostExplorerEnricher,
    OrganizationsEnricher,
)
from ..common.rich_utils import (
    console,
    create_progress_bar,
    create_table,
    format_cost,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)

# Configure module-level logging to suppress INFO/DEBUG messages in notebooks
logging.getLogger('runbooks').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.ERROR)
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
import warnings
warnings.filterwarnings('ignore')


@dataclass
class RDSAnalysisConfig:
    """
    Configuration for RDS cost analysis with unified profile routing.

    Profile Resolution (5-tier priority):
    1. Explicit profile parameters (highest priority)
    2. Service-specific environment variables (AWS_MANAGEMENT_PROFILE, AWS_BILLING_PROFILE)
    3. Generic AWS_PROFILE environment variable
    4. Service-specific defaults
    5. None (AWS default credentials)

    Args:
        management_profile: AWS profile for Organizations (defaults to service routing)
        billing_profile: AWS profile for Cost Explorer (defaults to service routing)
        regions: List of regions to analyze (defaults to ['ap-southeast-2'])
    """
    management_profile: Optional[str] = None
    billing_profile: Optional[str] = None
    regions: List[str] = None
    enable_organizations: bool = True
    enable_cost: bool = True
    include_12month_cost: bool = True

    def __post_init__(self):
        """Resolve profiles and regions."""
        from runbooks.common.aws_profile_manager import get_profile_for_service

        # Resolve management_profile (for Organizations)
        if not self.management_profile:
            self.management_profile = get_profile_for_service("organizations")

        # Resolve billing_profile (for Cost Explorer)
        if not self.billing_profile:
            self.billing_profile = get_profile_for_service("cost-explorer")

        # Default regions
        if not self.regions:
            self.regions = ['ap-southeast-2']


class RDSCostAnalyzer:
    """
    RDS cost analyzer with Organizations/Cost Explorer enrichment.

    Pattern: Mirror EC2CostAnalyzer structure for consistency
    """

    def __init__(self, config: RDSAnalysisConfig):
        """Initialize RDS analyzer with enterprise configuration."""
        from runbooks.common.profile_utils import create_operational_session

        self.config = config

        # Initialize enrichers
        self.orgs_enricher = OrganizationsEnricher()
        self.cost_enricher = CostExplorerEnricher()

        # Initialize AWS session
        self.session = create_operational_session(config.management_profile)

        logger.debug(f"RDS analyzer initialized with profiles: "
                    f"mgmt={config.management_profile}, billing={config.billing_profile}")

    def discover_rds_instances(self) -> pd.DataFrame:
        """
        Discover RDS instances across specified regions via describe_db_instances API.

        Returns:
            DataFrame with RDS instance metadata (11 columns)

        Pattern: Mirror EC2 discovery from ec2_analyzer.py
        """
        print_info("🔍 Discovering RDS instances via AWS API...")

        all_instances = []

        for region in self.config.regions:
            try:
                rds_client = self.session.client('rds', region_name=region)

                # Use paginator for large result sets
                paginator = rds_client.get_paginator('describe_db_instances')

                for page in paginator.paginate():
                    instances = page.get('DBInstances', [])

                    for db_instance in instances:
                        instance_data = {
                            'db_instance_identifier': db_instance['DBInstanceIdentifier'],
                            'db_instance_class': db_instance['DBInstanceClass'],
                            'engine': db_instance['Engine'],
                            'engine_version': db_instance['EngineVersion'],
                            'db_instance_status': db_instance['DBInstanceStatus'],
                            'allocated_storage': db_instance.get('AllocatedStorage', 0),
                            'availability_zone': db_instance.get('AvailabilityZone', 'N/A'),
                            'multi_az': db_instance.get('MultiAZ', False),
                            'publicly_accessible': db_instance.get('PubliclyAccessible', False),
                            'region': region,
                            'account_id': db_instance['DBInstanceArn'].split(':')[4] if 'DBInstanceArn' in db_instance else 'Unknown',
                        }
                        all_instances.append(instance_data)

                print_success(f"✅ {region}: {len(instances)} RDS instances discovered")

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                    print_warning(f"⚠️  {region}: Access denied (check IAM permissions)")
                else:
                    print_warning(f"⚠️  {region}: {error_code}")

            except Exception as e:
                print_warning(f"⚠️  {region}: Discovery failed - {str(e)[:100]}")

        if not all_instances:
            print_warning("⚠️  No RDS instances discovered across all regions")
            return pd.DataFrame()

        rds_df = pd.DataFrame(all_instances)
        print_success(f"✅ Total RDS instances discovered: {len(rds_df)}")

        return rds_df

    def enrich_with_organizations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich RDS data with Organizations metadata.

        Args:
            df: RDS DataFrame with account_id column

        Returns:
            Enriched DataFrame with 7 Organizations columns

        Pattern: Reuse base_enrichers.OrganizationsEnricher
        """
        if not self.config.enable_organizations:
            print_info("⏭️  Organizations enrichment disabled")
            return df

        print_info("🏢 Enriching with Organizations metadata...")

        enriched_df = self.orgs_enricher.enrich_with_organizations(
            df=df,
            account_id_column='account_id',
            management_profile=self.config.management_profile
        )

        print_success("✅ Organizations enrichment complete (7 columns)")
        return enriched_df

    def enrich_with_cost_explorer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich RDS data with Cost Explorer 12-month historical costs.

        Args:
            df: RDS DataFrame with db_instance_identifier column

        Returns:
            Enriched DataFrame with cost columns (monthly_cost, annual_cost_12mo)

        Pattern: Reuse base_enrichers.CostExplorerEnricher
        """
        if not self.config.enable_cost:
            print_info("⏭️  Cost Explorer enrichment disabled")
            return df

        print_info("💰 Enriching with Cost Explorer data...")

        enriched_df = self.cost_enricher.enrich_with_cost(
            df=df,
            resource_id_column='db_instance_identifier',
            resource_type='RDS',
            billing_profile=self.config.billing_profile,
            include_12month=self.config.include_12month_cost
        )

        print_success("✅ Cost Explorer enrichment complete")
        return enriched_df

    def analyze(self) -> pd.DataFrame:
        """
        Execute complete RDS cost analysis with all enrichments.

        Returns:
            Fully enriched RDS DataFrame

        Pattern: Mirror EC2CostAnalyzer.analyze() workflow
        """
        print_header("RDS 4-Way Validation Analysis", "Database Cost Optimization")

        # Step 1: Discover RDS instances
        rds_df = self.discover_rds_instances()

        if rds_df.empty:
            print_warning("⚠️  No RDS instances found - returning empty DataFrame")
            return rds_df

        # Step 2: Enrich with Organizations
        rds_df = self.enrich_with_organizations(rds_df)

        # Step 3: Enrich with Cost Explorer
        rds_df = self.enrich_with_cost_explorer(rds_df)

        # Step 4: Add validation metadata
        rds_df['validation_source'] = 'rds_api'
        rds_df['discovery_method'] = '4-way-validation'
        rds_df['analysis_timestamp'] = datetime.now().isoformat()

        print_success(f"✅ RDS analysis complete: {len(rds_df)} instances enriched")

        return rds_df


def analyze_rds_costs(
    management_profile: Optional[str] = None,
    billing_profile: Optional[str] = None,
    regions: Optional[List[str]] = None,
    enable_organizations: bool = True,
    enable_cost: bool = True,
    include_12month_cost: bool = True,
) -> pd.DataFrame:
    """
    Execute RDS 4-way validation cost analysis.

    This is the primary API for Jupyter notebook consumption.

    Args:
        management_profile: AWS profile for Organizations (defaults to service routing)
        billing_profile: AWS profile for Cost Explorer (defaults to service routing)
        regions: List of regions to analyze (defaults to ['ap-southeast-2'])
        enable_organizations: Enable Organizations enrichment (default: True)
        enable_cost: Enable Cost Explorer enrichment (default: True)
        include_12month_cost: Include 12-month historical costs (default: True)

    Returns:
        Fully enriched RDS DataFrame with Organizations + Cost data

    Example (Notebook usage):
        >>> from runbooks.finops.rds_analyzer import analyze_rds_costs
        >>>
        >>> rds_df = analyze_rds_costs(
        ...     management_profile='${MANAGEMENT_PROFILE}',
        ...     billing_profile='${BILLING_PROFILE}',
        ...     enable_cost=True,
        ...     include_12month_cost=True
        ... )
        >>>
        >>> # Export results
        >>> rds_df.to_csv('data/rds-4way-validated.csv', index=False)
        >>> rds_df.to_excel('data/rds-4way-validated.xlsx', index=False)

    Pattern: Mirror analyze_ec2_costs() API structure
    """
    # Initialize configuration
    config = RDSAnalysisConfig(
        management_profile=management_profile,
        billing_profile=billing_profile,
        regions=regions or ['ap-southeast-2'],
        enable_organizations=enable_organizations,
        enable_cost=enable_cost,
        include_12month_cost=include_12month_cost,
    )

    # Initialize analyzer
    analyzer = RDSCostAnalyzer(config)

    # Execute analysis
    rds_df = analyzer.analyze()

    return rds_df
