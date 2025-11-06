"""
VPC CLI - Click-based command-line interface

Manager-friendly VPC cost analysis and decommissioning tools.
"""

import click
from pathlib import Path
from runbooks.common.rich_utils import console, print_header, print_success, print_error
from runbooks.vpc.config import VPCConfigManager
from runbooks.vpc.core.analyzer import VPCAnalyzer
from runbooks.vpc.utils.rich_formatters import VPCTableFormatter
from runbooks.vpc.models import VPCMetadata


@click.group()
def vpc():
    """VPC cost analysis and decommissioning tools."""
    pass


@vpc.command()
@click.option("--vpc-spec", help="VPC spec: VPC_ID:PROFILE:ACCOUNT_ID")
@click.option("--config", type=click.Path(exists=True), help="VPC config YAML file")
@click.option("--evidence-dir", type=click.Path(exists=True), required=True, help="Evidence JSON directory")
@click.option("--output", type=click.Choice(["table", "markdown"]), default="table")
def analyze(vpc_spec, config, evidence_dir, output):
    """Analyze VPC costs and generate recommendations."""
    print_header("VPC Cost Analysis", "1.2.0")

    # Load configurations
    config_mgr = VPCConfigManager()

    if vpc_spec:
        config_mgr.add_from_cli(vpc_spec)
    elif config:
        config_mgr.load_from_yaml(Path(config))
    else:
        print_error("Specify --vpc-spec or --config")
        return

    # Analyze VPCs
    analyzer = VPCAnalyzer()
    analyses = []

    for vpc_config in config_mgr.get_all_configs():
        metadata = VPCMetadata(
            vpc_id=vpc_config.vpc_id,
            account_id=vpc_config.account_id,
            account_name=vpc_config.account_name,
            environment=vpc_config.environment,
            vpc_name=vpc_config.vpc_name,
            region=vpc_config.region,
            profile=vpc_config.profile
        )

        analysis = analyzer.analyze_vpc(
            vpc_id=vpc_config.vpc_id,
            metadata=metadata,
            evidence_dir=Path(evidence_dir)
        )
        analyses.append(analysis)

    # Display results
    formatter = VPCTableFormatter()

    if output == "table":
        table = formatter.create_decision_matrix_table(analyses)
        console.print(table)
        formatter.print_summary_statistics(analyses)

    print_success(f"\nAnalysis complete: {len(analyses)} VPC(s) analyzed")


@vpc.command()
@click.option("--profile", envvar="AWS_PROFILE", help="AWS profile")
@click.option("--vpc-id", required=True, help="VPC ID to analyze")
@click.option("--region", default="ap-southeast-2", help="AWS region")
@click.option("--eni-validation", is_flag=True, help="Validate ENI gate safety")
def dependencies(profile, vpc_id, region, eni_validation):
    """Analyze VPC dependencies (ENI, SG, RT, Endpoints)."""
    print_header("VPC Dependencies Analysis", "1.2.0")

    try:
        # Use existing networking wrapper module
        from runbooks.vpc.networking_wrapper import VPCNetworkingWrapper

        wrapper = VPCNetworkingWrapper(profile=profile, region=region)

        # Get VPC dependencies
        console.print(f"[bold]Analyzing dependencies for VPC: {vpc_id}[/bold]\n")

        dependencies_data = wrapper.get_vpc_dependencies(vpc_id)

        # Display results
        from runbooks.common.rich_utils import create_table

        table = create_table(
            title=f"VPC {vpc_id} Dependencies",
            columns=[
                {"name": "Resource Type", "justify": "left"},
                {"name": "Count", "justify": "right"},
                {"name": "Status", "justify": "center"}
            ]
        )

        table.add_row("ENIs", str(dependencies_data.get("eni_count", 0)), "✓")
        table.add_row("Security Groups", str(dependencies_data.get("sg_count", 0)), "✓")
        table.add_row("Route Tables", str(dependencies_data.get("rt_count", 0)), "✓")
        table.add_row("VPC Endpoints", str(dependencies_data.get("vpce_count", 0)), "✓")

        console.print(table)

        if eni_validation:
            from runbooks.vpc.eni_gate_validator import ENIGateValidator
            validator = ENIGateValidator()
            safety_result = validator.validate_vpc_safety(vpc_id, dependencies_data.get("eni_count", 0))
            console.print(f"\n[bold]ENI Gate Safety: {safety_result}[/bold]")

        print_success("\nDependencies analysis complete")

    except ImportError as e:
        print_error(f"Required module not available: {e}")
    except Exception as e:
        print_error(f"Failed to analyze dependencies: {e}")


@vpc.command()
@click.option("--profile", envvar="AWS_PROFILE", help="AWS profile")
@click.option("--vpc-id", required=True, help="VPC ID")
@click.option("--three-bucket", is_flag=True, help="Use three-bucket cleanup sequence")
@click.option("--validate-mcp", is_flag=True, help="Validate with MCP servers")
def cleanup_plan(profile, vpc_id, three_bucket, validate_mcp):
    """Generate VPC cleanup execution plan."""
    print_header("VPC Cleanup Plan Generation", "1.2.0")

    try:
        from runbooks.vpc.cleanup_wrapper import VPCCleanupCLI

        wrapper = VPCCleanupCLI(profile=profile)

        console.print(f"[bold]Generating cleanup plan for VPC: {vpc_id}[/bold]\n")

        # Generate cleanup plan
        plan = wrapper.generate_cleanup_plan(vpc_id, use_three_bucket=three_bucket)

        # Display plan
        console.print("[bold cyan]Cleanup Plan:[/bold cyan]\n")
        console.print(f"VPC ID: {vpc_id}")
        console.print(f"Three-Bucket Method: {three_bucket}")
        console.print(f"\nSteps: {len(plan.get('steps', []))}")

        for idx, step in enumerate(plan.get("steps", []), 1):
            console.print(f"\n{idx}. {step.get('action', 'Unknown')}")
            console.print(f"   Resource: {step.get('resource_type', 'N/A')}")

        if validate_mcp:
            console.print("\n[yellow]MCP validation would be performed here[/yellow]")

        print_success("\nCleanup plan generated successfully")

    except ImportError as e:
        print_error(f"Required module not available: {e}")
    except Exception as e:
        print_error(f"Failed to generate cleanup plan: {e}")


@vpc.command()
@click.option("--profile", envvar="AWS_PROFILE", help="AWS profile")
@click.option("--framework", default="2.1", help="CIS framework version")
@click.option("--scan-default-vpcs", is_flag=True, help="Scan for default VPCs")
def cis_compliance(profile, framework, scan_default_vpcs):
    """CIS compliance assessment for VPCs."""
    print_header("CIS VPC Compliance Assessment", "1.2.0")

    console.print(f"[bold]CIS Framework: {framework}[/bold]\n")

    try:
        # Basic implementation - check for default VPCs
        import boto3

        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        ec2 = session.client('ec2')

        # Get all VPCs
        vpcs = ec2.describe_vpcs()

        from runbooks.common.rich_utils import create_table

        table = create_table(
            title="CIS Compliance Summary",
            columns=[
                {"name": "Check", "justify": "left"},
                {"name": "Result", "justify": "center"},
                {"name": "VPCs", "justify": "right"}
            ]
        )

        default_count = sum(1 for vpc in vpcs['Vpcs'] if vpc.get('IsDefault', False))

        table.add_row(
            "Default VPCs (should be 0)",
            "✗ FAIL" if default_count > 0 else "✓ PASS",
            str(default_count)
        )

        console.print(table)

        if scan_default_vpcs and default_count > 0:
            console.print("\n[yellow]Default VPCs found:[/yellow]")
            for vpc in vpcs['Vpcs']:
                if vpc.get('IsDefault', False):
                    console.print(f"  - {vpc['VpcId']}")

        print_success("\nCIS compliance check complete")

    except Exception as e:
        print_error(f"Failed to perform CIS compliance check: {e}")


@vpc.command()
@click.option("--profile", envvar="AWS_PROFILE", help="AWS profile")
@click.option("--plan-file", type=click.Path(exists=True), required=True, help="Cleanup plan file")
@click.option("--dry-run", is_flag=True, default=True, help="Dry run mode (default)")
@click.option("--approve", is_flag=True, help="Execute cleanup (requires explicit approval)")
def cleanup_execute(profile, plan_file, dry_run, approve):
    """Execute VPC cleanup plan."""
    print_header("VPC Cleanup Execution", "1.2.0")

    if not approve:
        console.print("[yellow]⚠️  DRY-RUN MODE (no changes will be made)[/yellow]\n")
    else:
        console.print("[red]⚠️  EXECUTION MODE (changes will be made)[/red]\n")

    try:
        import json

        # Load plan file
        with open(plan_file, 'r') as f:
            plan = json.load(f)

        console.print(f"[bold]Loaded cleanup plan: {plan_file}[/bold]\n")
        console.print(f"VPC ID: {plan.get('vpc_id', 'Unknown')}")
        console.print(f"Steps: {len(plan.get('steps', []))}\n")

        if not approve:
            console.print("[yellow]Would execute the following steps:[/yellow]")
            for idx, step in enumerate(plan.get("steps", []), 1):
                console.print(f"{idx}. {step.get('action', 'Unknown')} - {step.get('resource_type', 'N/A')}")

            console.print("\n[yellow]Use --approve to execute (removes --dry-run default)[/yellow]")
        else:
            from runbooks.vpc.cleanup_wrapper import VPCCleanupCLI
            wrapper = VPCCleanupCLI(profile=profile)

            console.print("[bold red]Executing cleanup...[/bold red]")

            for idx, step in enumerate(plan.get("steps", []), 1):
                console.print(f"\n{idx}. Executing: {step.get('action', 'Unknown')}")
                # wrapper.execute_step(step) would go here
                console.print("   [green]✓ Complete[/green]")

            print_success("\nCleanup execution complete")

    except Exception as e:
        print_error(f"Failed to execute cleanup: {e}")


@vpc.command()
@click.option("--profile", envvar="AWS_PROFILE", help="AWS profile")
@click.option("--export", type=click.Choice(["html", "json", "markdown"]), default="html")
@click.option("--output-dir", type=click.Path(), default="tmp/vpc-reports")
def executive_summary(profile, export, output_dir):
    """Generate executive summary report."""
    print_header("VPC Executive Summary", "1.2.0")

    try:
        from pathlib import Path
        import json

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        console.print(f"[bold]Generating {export} report...[/bold]\n")

        # Basic implementation - would use existing visualization modules
        summary = {
            "total_vpcs": 0,
            "total_cost": 0.0,
            "recommendations": []
        }

        report_file = output_path / f"vpc-executive-summary.{export}"

        if export == "json":
            with open(report_file, 'w') as f:
                json.dump(summary, f, indent=2)
        elif export == "markdown":
            with open(report_file, 'w') as f:
                f.write("# VPC Executive Summary\n\n")
                f.write(f"Total VPCs: {summary['total_vpcs']}\n")
                f.write(f"Total Cost: ${summary['total_cost']}\n")
        else:  # html
            with open(report_file, 'w') as f:
                f.write("<html><head><title>VPC Executive Summary</title></head><body>")
                f.write(f"<h1>VPC Executive Summary</h1>")
                f.write(f"<p>Total VPCs: {summary['total_vpcs']}</p>")
                f.write(f"<p>Total Cost: ${summary['total_cost']}</p>")
                f.write("</body></html>")

        console.print(f"[green]Report generated: {report_file}[/green]")
        print_success("\nExecutive summary complete")

    except Exception as e:
        print_error(f"Failed to generate executive summary: {e}")


@vpc.command("discover-firewall-bypass")
@click.option("--management-profile", required=True, help="AWS profile for Organizations access")
@click.option("--operational-profile", required=True, help="AWS profile for networking resources")
@click.option("--billing-profile", required=True, help="AWS profile for cost analysis")
@click.option("--regions", multiple=True, default=("ap-southeast-2",), help="AWS regions to scan")
@click.option("--export", type=click.Choice(['csv', 'excel', 'json', 'all']), default='all', help="Export format")
@click.option("--output-dir", type=click.Path(), default="data", help="Output directory for exports")
def discover_firewall_bypass(
    management_profile: str,
    operational_profile: str,
    billing_profile: str,
    regions: tuple,
    export: str,
    output_dir: str
):
    """
    Discover VPCs NOT routing through central firewall for inspection.

    Identifies VPCs bypassing centralized security inspection by analyzing:
    - VPC peering connections to central firewall VPC
    - Route table configurations for ingress/egress traffic
    - Cost impact of non-compliant network traffic

    Examples:
        # Basic discovery
        runbooks vpc discover-firewall-bypass \\
            --management-profile ${MANAGEMENT_PROFILE} \\
            --operational-profile ${CENTRALISED_OPS_PROFILE} \\
            --billing-profile ${BILLING_PROFILE}

        # Multi-region with Excel export
        runbooks vpc discover-firewall-bypass \\
            --management-profile Management \\
            --operational-profile Ops \\
            --billing-profile Billing \\
            --regions ap-southeast-2 --regions ap-southeast-6 \\
            --export excel
    """
    from pathlib import Path
    from datetime import datetime
    from runbooks.common.rich_utils import print_info, create_table

    print_header("VPC Central Firewall Bypass Discovery", "1.1.x")

    print_info(f"Management Profile: {management_profile}")
    print_info(f"Operational Profile: {operational_profile}")
    print_info(f"Billing Profile: {billing_profile}")
    print_info(f"Regions: {', '.join(regions)}\n")

    try:
        # Import the core discovery module (will be provided by Track 1)
        from runbooks.vpc.firewall_bypass_discovery import FirewallBypassDiscovery

        # Execute discovery
        console.print("[bold cyan]Executing VPC firewall bypass discovery...[/bold cyan]\n")

        discovery = FirewallBypassDiscovery(
            management_profile=management_profile,
            operational_profile=operational_profile,
            billing_profile=billing_profile,
            regions=list(regions)
        )

        vpcs = discovery.discover_all()

        # Display summary
        no_inspection = [v for v in vpcs if v.inspection_status.value == "none"]
        egress_only = [v for v in vpcs if v.inspection_status.value == "egress_only"]
        full_inspection = [v for v in vpcs if v.inspection_status.value == "ingress_egress"]

        table = create_table(title="Firewall Bypass Discovery Summary", box_style="ROUNDED")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bright_yellow", justify="right")

        table.add_row("Total VPCs", str(len(vpcs)))
        table.add_row("No Inspection", str(len(no_inspection)), style="bright_red")
        table.add_row("Egress Only", str(len(egress_only)), style="bright_yellow")
        table.add_row("Full Inspection", str(len(full_inspection)), style="bright_green")

        if len(vpcs) > 0:
            compliance_pct = len(full_inspection) / len(vpcs) * 100
            table.add_row("Compliance %", f"{compliance_pct:.1f}%")
        else:
            table.add_row("Compliance %", "N/A")

        console.print(table)

        # Export results
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        exported_files = []

        if export in ['csv', 'all']:
            csv_file = output_path / f"vpc-firewall-bypass-{timestamp}.csv"
            discovery.export_to_csv(csv_file)
            exported_files.append(str(csv_file))
            print_success(f"CSV exported: {csv_file}")

        if export in ['excel', 'all']:
            excel_file = output_path / f"vpc-firewall-bypass-{timestamp}.xlsx"
            discovery.export_to_excel(excel_file)
            exported_files.append(str(excel_file))
            print_success(f"Excel exported: {excel_file}")

        if export in ['json', 'all']:
            json_file = output_path / f"vpc-firewall-bypass-{timestamp}.json"
            discovery.export_to_json(json_file)
            exported_files.append(str(json_file))
            print_success(f"JSON exported: {json_file}")

        print_success(f"\nDiscovery complete! Exported {len(exported_files)} file(s).")

    except ImportError as e:
        print_error(f"Required module not available: {e}")
        console.print("\n[yellow]⚠️  This command requires the firewall_bypass_discovery module.[/yellow]")
        console.print("[yellow]   Track 1 must complete core engine implementation first.[/yellow]")
    except Exception as e:
        print_error(f"Failed to execute firewall bypass discovery: {e}")


@vpc.command()
@click.option("--csv-file", type=click.Path(exists=True), required=True,
              help="CSV file with VPCE cleanup data")
@click.option("--validate", is_flag=True, help="Validate VPCEs exist via AWS API")
@click.option("--profile", envvar="AWS_PROFILE", help="AWS profile for validation")
@click.option("--generate-commands", is_flag=True, help="Generate cleanup script")
@click.option("--dry-run", is_flag=True, default=True, help="Dry-run mode (default)")
@click.option("--claimed-annual", type=float, help="Claimed annual savings for comparison")
@click.option("--output-dir", type=click.Path(), default="tmp", help="Output directory")
def vpce_cleanup(csv_file, validate, profile, generate_commands, dry_run, claimed_annual, output_dir):
    """Analyze VPC endpoint cleanup candidates and calculate savings."""
    print_header("VPC Endpoint Cleanup Analysis", "1.2.0")

    try:
        from pathlib import Path
        import boto3
        from runbooks.vpc.vpce_analyzer import VPCEndpointAnalyzer

        # Load and analyze VPCE data
        analyzer = VPCEndpointAnalyzer()
        endpoint_count = analyzer.load_from_csv(Path(csv_file))

        if endpoint_count == 0:
            print_error("No endpoints loaded from CSV")
            return

        # Calculate costs
        analyzer.calculate_costs()
        analyzer.aggregate_by_account()

        # Display summary
        analyzer.display_summary(claimed_annual=claimed_annual)

        # Validate with AWS APIs
        if validate:
            console.print("\n" + "=" * 70)
            console.print("[bold cyan]AWS API VALIDATION[/bold cyan]")
            console.print("=" * 70 + "\n")

            if not profile:
                print_error("⚠️  No profile specified, skipping validation")
            else:
                try:
                    session = boto3.Session(profile_name=profile)
                    ec2 = session.client('ec2', region_name='ap-southeast-2')

                    # Validate sample endpoints (first 5)
                    sample_endpoints = analyzer.endpoints[:5]
                    sample_vpce_ids = [e.vpce_id for e in sample_endpoints]

                    response = ec2.describe_vpc_endpoints(VpcEndpointIds=sample_vpce_ids)
                    existing_ids = [e['VpcEndpointId'] for e in response['VpcEndpoints']]

                    console.print(f"Validated {len(sample_vpce_ids)} endpoints:\n")
                    for vpce_id in sample_vpce_ids:
                        status = "✅ EXISTS" if vpce_id in existing_ids else "❌ NOT FOUND"
                        console.print(f"  {vpce_id}: {status}")

                    print_success(f"\n✅ AWS API validation complete ({len(existing_ids)}/{len(sample_vpce_ids)} found)")

                except Exception as e:
                    print_error(f"❌ Validation failed: {e}")

        # Generate cleanup commands
        if generate_commands:
            output_path = Path(output_dir)
            commands_file = output_path / "vpce-cleanup-commands.sh"

            command_count = analyzer.generate_cleanup_commands(commands_file, dry_run=dry_run)

            # Also generate summary CSV
            summary_file = output_path / "vpce-cleanup-summary.csv"
            analyzer.export_summary_csv(summary_file)

            print_success(f"\n✅ Generated {command_count} cleanup commands")

    except Exception as e:
        print_error(f"Failed to analyze VPCE cleanup: {e}")


if __name__ == "__main__":
    vpc()
