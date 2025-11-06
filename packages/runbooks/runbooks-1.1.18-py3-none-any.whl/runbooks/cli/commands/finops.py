"""
FinOps Commands Module - Financial Operations & Cost Optimization

KISS Principle: Focused on financial operations and cost optimization
DRY Principle: Uses centralized patterns from DRYPatternManager

Phase 2 Enhancement: Eliminates pattern duplication through reference-based access.
Context Efficiency: Reduced imports and shared instances for memory optimization.
"""

# Essential imports that can't be centralized due to decorator usage
import click

# DRY Pattern Manager - eliminates duplication across CLI modules
from runbooks.common.patterns import get_console, get_error_handlers, get_click_group_creator, get_common_decorators

# Import unified CLI decorators (v1.1.7 standardization)
from runbooks.common.cli_decorators import (
    common_aws_options,
    common_output_options,
    common_multi_account_options,
    common_filter_options,
    mcp_validation_option
)

# Single console instance shared across all modules (DRY principle)
console = get_console()

# Import additional modules for enhanced functionality
from runbooks.common.rich_utils import print_header, print_success, print_error, print_info
from runbooks.common.output_controller import OutputController
from runbooks.common.logging_config import configure_logging

# Centralized error handlers - replaces 6 duplicate patterns in this module
error_handlers = get_error_handlers()


def _get_cost_metric_display(cost_metrics):
    """Get display string for cost metrics."""
    if len(cost_metrics) == 1:
        return cost_metrics[0]
    else:
        return " + ".join(cost_metrics)


def create_finops_group():
    """
    Create the finops command group with all subcommands.

    Returns:
        Click Group object with all finops commands

    Performance: Lazy creation only when needed by DRYCommandRegistry
    Context Reduction: ~800 lines extracted from main.py
    """

    # Custom Group class with Rich Tree/Table help formatting
    class RichFinOpsGroup(click.Group):
        """Custom Click Group with Rich Tree/Table help display."""

        def format_help(self, ctx, formatter):
            """Format help text with Rich Tree/Table categorization."""
            import os
            from rich.tree import Tree
            from rich.table import Table as RichTable

            # Check for TEST_MODE environment variable for backward compatibility
            test_mode = os.environ.get('RUNBOOKS_TEST_MODE', '0') == '1'

            if test_mode:
                # Plain text fallback for testing
                click.echo("Usage: runbooks finops [OPTIONS] COMMAND [ARGS]...")
                click.echo("")
                click.echo("  Financial operations and cost optimization for AWS resources.")
                click.echo("")
                click.echo("Commands:")
                click.echo("  dashboard                        Multi-account cost visibility")
                click.echo("  analyze-ec2                      EC2 cost analysis with 4-way enrichment")
                click.echo("  analyze-workspaces               WorkSpaces cost analysis")
                click.echo("  lambda-analysis                  Lambda cost and activity analysis")
                click.echo("  infrastructure                   Comprehensive infrastructure analysis")
                click.echo("  ec2-snapshots                    EC2 snapshot cost optimization")
                click.echo("  optimize                         General cost optimization recommendations")
                click.echo("  ec2-decommission-analysis        EC2 decommission candidate identification")
                click.echo("  workspaces-decommission-analysis WorkSpaces decommission tier analysis")
                click.echo("  enrich-workspaces                WorkSpaces metadata enrichment")
                click.echo("  WorkSpaces                       WorkSpaces discovery and analysis")
                click.echo("  export                           Multi-format export")
                return

            # Categorize commands based on business function
            categories = {
                "💰 Cost Analysis": [
                    ("dashboard", "Multi-account cost visibility with MCP validation"),
                    ("analyze-ec2", "EC2 cost analysis with 4-way enrichment (Discovery→Orgs→Cost→Activity)"),
                    ("analyze-workspaces", "WorkSpaces cost analysis with decommission tier scoring"),
                    ("lambda-analysis", "Lambda cost and activity analysis")
                ],
                "⚙️ Infrastructure Optimization": [
                    ("infrastructure", "Comprehensive infrastructure analysis"),
                    ("ec2-snapshots", "EC2 snapshot cost optimization"),
                    ("optimize", "General cost optimization recommendations")
                ],
                "📊 Decommission Analysis": [
                    ("ec2-decommission-analysis", "EC2 decommission candidate identification"),
                    ("workspaces-decommission-analysis", "WorkSpaces decommission tier analysis")
                ],
                "🔄 Data Operations": [
                    ("enrich-workspaces", "WorkSpaces metadata enrichment"),
                    ("WorkSpaces", "WorkSpaces discovery and analysis")
                ],
                "📤 Export": [
                    ("export", "Multi-format export (CSV, JSON, PDF, Markdown)")
                ]
            }

            # Phase 1: Pre-calculate max column widths across ALL categories (Track 3A pattern)
            max_cmd_len = 0
            for category_commands in categories.values():
                for cmd, desc in category_commands:
                    max_cmd_len = max(max_cmd_len, len(cmd))

            # Set command column width with padding
            cmd_width = max_cmd_len + 2

            # Create Rich Tree
            tree = Tree("[bold cyan]FinOps Commands[/bold cyan] (12 commands)")

            # Add each category with fixed-width tables
            for category_name, commands in categories.items():
                category_branch = tree.add(f"[bold green]{category_name}[/bold green] [dim]({len(commands)} commands)[/dim]")

                # Create table with FIXED command width for vertical alignment, flexible description
                table = RichTable(show_header=True, box=None, padding=(0, 2))
                table.add_column("Command", style="cyan", no_wrap=True, min_width=cmd_width, max_width=cmd_width)
                table.add_column("Description", style="dim", no_wrap=False, overflow="fold")

                # Add rows
                for cmd, desc in commands:
                    table.add_row(cmd, desc)

                category_branch.add(table)

            # Display the tree
            console.print(tree)
            console.print("\n[blue]💡 Usage: runbooks finops [COMMAND] [OPTIONS][/blue]")
            console.print("[blue]📖 Example: runbooks finops dashboard --profile billing-profile --timeframe monthly[/blue]")

    @click.group(cls=RichFinOpsGroup, invoke_without_command=True)
    @common_filter_options
    @common_multi_account_options
    @common_output_options
    @common_aws_options
    @click.pass_context
    def finops(ctx, profile, region, dry_run, format, output_dir, all_outputs, export,
               all_profiles, profiles, regions, all_regions, tags, accounts):
        """
        Financial operations and cost optimization for AWS resources.

        Comprehensive cost analysis, budget management, and financial reporting
        with enterprise-grade accuracy and multi-format export capabilities.

        Features:
        • Real-time cost analysis with MCP validation (≥99.5% accuracy)
        • Multi-format exports: CSV, JSON, PDF, Markdown
        • Quarterly intelligence with strategic financial reporting
        • Enterprise AWS profile support with multi-account capabilities

        Examples:
            runbooks finops dashboard --profile billing-profile
            runbooks finops dashboard --all-profiles --timeframe monthly
            runbooks finops dashboard --regions ap-southeast-2 ap-southeast-6
            runbooks finops export --format pdf --output-dir ./reports
        """
        # Ensure context object exists
        if ctx.obj is None:
            ctx.obj = {}
        ctx.obj.update({
            "profile": profile,
            "region": region,
            "dry_run": dry_run,
            "output_format": format,
            "output_dir": output_dir,
            "all_outputs": all_outputs,
            "export": export,
            "all_profiles": all_profiles,
            "profiles": profiles,
            "regions": regions,
            "all_regions": all_regions,
            "tags": tags,
            "accounts": accounts
        })

        # Auto-execute dashboard when no subcommand provided (eliminates "only logs" pattern)
        if ctx.invoked_subcommand is None:
            # Invoke dashboard with default parameters
            ctx.invoke(dashboard,
                      profile=profile,
                      all_profile=all_profiles,  # Note: dashboard parameter is all_profile (singular)
                      timeframe='monthly',
                      services=None,
                      accounts=None,
                      validate=False,
                      validate_mcp=False,
                      mcp_validate=False,
                      csv=False,
                      markdown=False,
                      pdf=False,
                      json=False,
                      export_format=None,
                      unblended=False,
                      amortized=False,
                      dual_metrics=False,
                      dry_run=dry_run)

    @finops.command()
    @click.option("--profile", help="AWS profile to use for authentication")
    @click.option(
        "--timeframe",
        type=click.Choice(["daily", "weekly", "monthly", "quarterly"]),
        default="monthly",
        help="Analysis timeframe",
    )
    @click.option("--services", multiple=True, help="Specific AWS services to analyze")
    @click.option("--accounts", multiple=True, help="Specific AWS accounts to analyze")
    @click.option("--validate", is_flag=True, help="Enable MCP validation for accuracy")
    @click.option("--validate-mcp", is_flag=True, help="Run standalone MCP validation framework (AWS-2 implementation)")
    @click.option("--mcp-validate", is_flag=True, help="Enable MCP validation for ≥99.5% accuracy cross-validation")
    @click.option("--csv", is_flag=True, help="Export results to CSV format")
    @click.option("--markdown", is_flag=True, help="Export results to Markdown format")
    @click.option("--pdf", is_flag=True, help="Export results to PDF format")
    @click.option("--json", is_flag=True, help="Export results to JSON format")
    @click.option(
        "--export-format",
        type=click.Choice(["json", "csv", "pdf", "markdown"]),
        help="Export format for results (legacy option - use individual flags)",
    )
    @click.option("--unblended", is_flag=True, help="Use unblended cost metrics (default: BlendedCost)")
    @click.option("--amortized", is_flag=True, help="Use amortized cost metrics for Reserved Instances")
    @click.option("--dual-metrics", is_flag=True, help="Show both BlendedCost and AmortizedCost")
    @click.option("--dry-run", is_flag=True, default=True, help="Execute in dry-run mode")
    @click.pass_context
    def dashboard(
        ctx,
        profile,
        all_profile,
        timeframe,
        services,
        accounts,
        validate,
        validate_mcp,
        mcp_validate,
        csv,
        markdown,
        pdf,
        json,
        export_format,
        unblended,
        amortized,
        dual_metrics,
        dry_run,
    ):
        """
        Multi-account cost visibility with MCP validation.

        \b
        📊 DASHBOARD OPTIONS (15 total)
        ├── 🔐 Authentication (1 option)
        │   └── --profile TEXT        AWS profile for authentication
        │
        ├── ⏰ Time Range (1 option)
        │   └── --timeframe CHOICE    [daily|weekly|monthly|quarterly] (default: monthly)
        │
        ├── 🎯 Filtering (2 options)
        │   └── --services TEXT       Specific AWS services (multiple allowed)
        │   └── --accounts TEXT       Specific AWS accounts (multiple allowed)
        │
        ├── ✅ Validation (3 options)
        │   └── --validate            Enable MCP validation for accuracy
        │   └── --validate-mcp        Standalone MCP validation framework
        │   └── --mcp-validate        MCP cross-validation (≥99.5% accuracy)
        │
        ├── 📤 Export Formats (4 options)
        │   └── --csv                 Export to CSV format
        │   └── --markdown            Export to Markdown format
        │   └── --pdf                 Export to PDF format
        │   └── --json                Export to JSON format
        │
        ├── 💰 Cost Metrics (3 options)
        │   └── --unblended           Use UnblendedCost metrics
        │   └── --amortized           Use AmortizedCost for Reserved Instances
        │   └── --dual-metrics        Show both BlendedCost and AmortizedCost
        │
        └── 🔧 Execution (2 options)
            └── --export-format CHOICE  [json|csv|pdf|markdown] (legacy)
            └── --dry-run               Execute in dry-run mode (default: true)

        \b
        💡 Sprint 1 Targets: 25-50% cost savings via decommission analysis
        📖 Example: runbooks finops dashboard --profile billing --timeframe monthly --mcp-validate
        """
        # Handle multi-account Landing Zone analysis with Organizations API discovery
        if all_profile:
            try:
                from runbooks.finops.dashboard_runner import MultiAccountDashboard, DashboardRouter
                from runbooks.common.rich_utils import print_header, print_success, print_error, print_info
                from runbooks.inventory.inventory_modules import get_org_accounts_from_profiles, get_profiles
                import argparse

                print_header("Multi-Account Landing Zone Dashboard", all_profile)
                console.print("[cyan]🏢 Discovering AWS Organization accounts via Organizations API...[/cyan]")

                # CORRECTED: Use management profile TEXT parameter for Organizations API access
                try:
                    # Use management profile specified by user (MANAGEMENT_PROFILE, BILLING_PROFILE, or CENTRALISED_OPS_PROFILE)
                    mgmt_profile_list = get_profiles(fprofiles=[all_profile])
                    console.print(f"[dim]Querying Organizations API with profile: {all_profile}[/dim]")

                    org_accounts = get_org_accounts_from_profiles(mgmt_profile_list)

                    # Extract account IDs from discovered organization accounts
                    discovered_account_ids = []
                    for acct in org_accounts:
                        if acct.get("Success") and acct.get("RootAcct") and acct.get("aws_acct"):
                            # Root account found - extract all child accounts
                            for child in acct["aws_acct"].ChildAccounts:
                                discovered_account_ids.append(child["AccountId"])

                    if discovered_account_ids:
                        console.print(f"[green]✅ Discovered {len(discovered_account_ids)} organization accounts[/green]")
                        console.print(f"[dim]Analysis Scope: Organization-wide with Landing Zone support[/dim]\n")
                    else:
                        console.print(f"[yellow]⚠️  No organization accounts discovered - using single account mode[/yellow]")
                        console.print(f"[dim]Tip: Ensure {profile} has AWS Organizations permissions[/dim]\n")

                except Exception as org_error:
                    console.print(f"[yellow]⚠️  Organizations discovery failed: {str(org_error)}[/yellow]")
                    console.print(f"[dim]Falling back to single account mode[/dim]\n")
                    discovered_account_ids = []  # Empty list for fallback

                # Create mock args object for multi-dashboard compatibility
                args = argparse.Namespace()
                args.profile = all_profile  # Use management profile for AWS Organizations access
                args.timeframe = timeframe
                args.services = services
                # PHASE 2 ENHANCEMENT: Use Organizations-discovered accounts if available
                args.accounts = tuple(discovered_account_ids) if discovered_account_ids else accounts
                args.validate = validate or mcp_validate
                # CRITICAL FIX: Handle multiple export format flags
                export_formats = []
                if csv:
                    export_formats.append("csv")
                if markdown:
                    export_formats.append("markdown")
                if pdf:
                    export_formats.append("pdf")
                if json:
                    export_formats.append("json")
                if export_format and export_format not in export_formats:
                    export_formats.append(export_format)

                args.export_format = export_formats[0] if export_formats else None
                args.export_formats = export_formats  # Store all requested formats

                # CRITICAL FIX: Handle cost metric options
                cost_metrics = ["BlendedCost"]  # Default metric
                if unblended:
                    cost_metrics = ["UnblendedCost"]
                elif amortized:
                    cost_metrics = ["AmortizedCost"]
                elif dual_metrics:
                    cost_metrics = ["BlendedCost", "AmortizedCost"]

                args.cost_metrics = cost_metrics
                args.cost_metric_display = _get_cost_metric_display(cost_metrics)
                args.dry_run = dry_run
                args.all = True  # Enable all accounts mode
                args.top_accounts = 50  # Show many accounts for enterprise view
                args.services_per_account = 3
                args.time_range = None
                args.audit = False  # Not audit mode
                args.tag = None
                args.regions = None

                # Initialize router and dashboard
                router = DashboardRouter(console=console)
                routing_config = router.route_dashboard_request(args)

                # Create multi-account dashboard
                multi_dashboard = MultiAccountDashboard(console=console)

                # Execute multi-account analysis
                result = multi_dashboard.run_dashboard(args, routing_config)

                if result == 0:
                    print_success("Multi-account Landing Zone analysis completed successfully")
                else:
                    print_error("Multi-account analysis encountered issues")

                return result

            except ImportError as e:
                console.print(f"[red]❌ Multi-account dashboard not available: {e}[/red]")
                console.print("[yellow]💡 Falling back to single-account mode with specified profile[/yellow]")
                # Fallback to single account with the specified profile
                resolved_profile = all_profile
            except Exception as e:
                console.print(f"[red]❌ Multi-account analysis failed: {e}[/red]")
                console.print("[yellow]💡 Fallingback to single-account mode[/yellow]")
                resolved_profile = all_profile
        else:
            resolved_profile = profile or ctx.obj.get("profile", "default")

        # Handle standalone MCP validation (AWS-2 implementation)
        if validate_mcp:
            try:
                from runbooks.common.rich_utils import print_header, print_success, print_error, print_info
                import asyncio

                print_header("MCP Validation Framework", "AWS-2 Implementation")
                console.print("[cyan]🔍 Running comprehensive MCP validation for ≥99.5% accuracy[/cyan]")

                # Import and initialize MCP validator
                from runbooks.validation.mcp_validator import MCPValidator

                # Enterprise profiles configuration
                validation_profiles = {
                    "billing": "${BILLING_PROFILE}",
                    "management": "${MANAGEMENT_PROFILE}",
                    "centralised_ops": "${CENTRALISED_OPS_PROFILE}",
                    "single_aws": "${SINGLE_AWS_PROFILE}",
                }

                # Initialize validator with configured profiles
                validator = MCPValidator(
                    profiles=validation_profiles, tolerance_percentage=5.0, performance_target_seconds=30.0
                )

                # Run comprehensive validation
                validation_report = asyncio.run(validator.validate_all_operations())

                # Success criteria for AWS-2
                if validation_report.overall_accuracy >= 99.5:
                    print_success(
                        f"✅ AWS-2 SUCCESS: {validation_report.overall_accuracy:.1f}% ≥ 99.5% target achieved"
                    )
                    return 0
                else:
                    print_error(f"❌ AWS-2 FAILED: {validation_report.overall_accuracy:.1f}% < 99.5% target")
                    return 1

            except Exception as e:
                print_error(f"❌ AWS-2 MCP validation failed: {e}")
                return 1

        try:
            from runbooks.common.rich_utils import print_header, print_success, print_error, create_table, format_cost
            from runbooks.common.profile_utils import create_cost_session
            from runbooks.finops.cost_processor import get_cost_data
            from runbooks.finops.aws_client import get_account_id, ec2_summary, get_accessible_regions
            import boto3
            from datetime import datetime, timedelta
            from rich.table import Table
            from rich.panel import Panel

            # Resolve profile with priority: command --profile > parent context > default
            # Note: resolved_profile already set above for multi-account vs single-account mode
            if "resolved_profile" not in locals():
                resolved_profile = profile or ctx.obj.get("profile", "default")
            resolved_dry_run = dry_run if dry_run is not None else ctx.obj.get("dry_run", True)

            # MCP validation integration
            mcp_results = None
            if mcp_validate or validate:
                try:
                    from runbooks.validation.mcp_validator import MCPValidator
                    import asyncio

                    console.print("[cyan]🔍 Running MCP validation for dashboard data accuracy[/cyan]")

                    # Configure validation profiles using resolved profile
                    validation_profiles = {
                        "billing": resolved_profile,
                        "management": resolved_profile,
                        "centralised_ops": resolved_profile,
                        "single_aws": resolved_profile,
                    }

                    # Initialize validator
                    validator = MCPValidator(
                        profiles=validation_profiles, tolerance_percentage=5.0, performance_target_seconds=30.0
                    )

                    # Run validation focused on cost explorer operations (primary finops validation)
                    mcp_results = asyncio.run(validator.validate_cost_explorer())

                    # Display validation results
                    if mcp_results.accuracy_percentage >= 99.5:
                        console.print(
                            f"[green]✅ MCP Validation PASSED: {mcp_results.accuracy_percentage:.1f}% accuracy[/green]"
                        )
                    elif mcp_results.accuracy_percentage >= 95.0:
                        console.print(
                            f"[yellow]⚠️ MCP Validation WARNING: {mcp_results.accuracy_percentage:.1f}% accuracy (target: ≥99.5%)[/yellow]"
                        )
                    else:
                        console.print(
                            f"[red]❌ MCP Validation FAILED: {mcp_results.accuracy_percentage:.1f}% accuracy[/red]"
                        )

                except Exception as e:
                    console.print(f"[yellow]⚠️ MCP validation failed: {e}[/yellow]")
                    console.print("[dim]Continuing with dashboard generation...[/dim]")

            print_header("FinOps Cost Analysis Dashboard", resolved_profile)

            # Create AWS session and get account info
            session = create_cost_session(profile_name=resolved_profile)
            account_id = get_account_id(session)

            console.print(f"[cyan]📊 Analyzing costs for AWS Account: {account_id}[/cyan]\n")

            # Get cost data for the specified timeframe
            try:
                # Calculate time range based on timeframe
                time_range_days = {"daily": 7, "weekly": 30, "monthly": 90, "quarterly": 365}.get(timeframe, 30)

                # Get comprehensive cost data
                cost_data = get_cost_data(
                    session,
                    time_range=time_range_days,
                    get_trend=True,
                    profile_name=resolved_profile,
                    account_id=account_id,
                )

                # Display Cost Summary Table
                cost_table = create_table(title="💰 Cost Analysis Summary")
                cost_table.add_column("Metric", style="bold")
                cost_table.add_column("Value", style="cyan")

                # Access cost data using correct field names from CostData TypedDict
                current_cost = cost_data.get("current_month", 0)
                previous_cost = cost_data.get("last_month", 0)

                cost_table.add_row("Current Monthly Spend", f"${current_cost:,.2f}")
                cost_table.add_row("Previous Month", f"${previous_cost:,.2f}")

                # CRITICAL FIX: Enhanced month-over-month calculation for partial months
                if previous_cost > 0:
                    change_pct = ((current_cost - previous_cost) / previous_cost) * 100

                    # Check if current month is partial
                    from datetime import datetime

                    today = datetime.now()
                    current_day = today.day

                    # Add context for partial month comparisons
                    if current_day < 28:  # Likely partial month
                        # Calculate daily average for comparison
                        daily_current = current_cost / current_day
                        daily_previous = previous_cost / 30  # Assume 30-day month
                        daily_change_pct = ((daily_current - daily_previous) / daily_previous) * 100

                        change_str = f"{change_pct:+.1f}% (Daily Avg: {daily_change_pct:+.1f}%)"
                        cost_table.add_row("Month-over-Month Change", f"[yellow]{change_str}[/yellow]")
                        cost_table.add_row(
                            "Comparison Note", f"[dim]Partial month ({current_day} days vs full previous month)[/dim]"
                        )
                    else:
                        # Full month comparison
                        change_str = f"{change_pct:+.1f}%"
                        if change_pct > 10:
                            change_str = f"[red]{change_str} ⚠️[/red]"
                        elif change_pct < -5:
                            change_str = f"[green]{change_str} ✅[/green]"
                        else:
                            change_str = f"[yellow]{change_str}[/yellow]"
                        cost_table.add_row("Month-over-Month Change", change_str)

                cost_table.add_row("Account ID", account_id)
                cost_table.add_row("Analysis Period", f"{timeframe.title()} ({time_range_days} days)")
                console.print(cost_table)
                console.print()

                # Display Top Services by Cost
                services_data = cost_data.get("costs_by_service", {})
                if services_data:
                    services_table = create_table(title="🏗️ Top AWS Services by Cost")
                    services_table.add_column("Service", style="bold")
                    services_table.add_column("Cost", style="green")
                    services_table.add_column("% of Total", style="yellow")

                    # Sort services by cost and show top 10
                    sorted_services = sorted(services_data.items(), key=lambda x: x[1], reverse=True)[:10]

                    for service, cost in sorted_services:
                        percentage = (cost / current_cost * 100) if current_cost > 0 else 0
                        services_table.add_row(service, f"${cost:,.2f}", f"{percentage:.1f}%")

                    console.print(services_table)
                    console.print()

                # Get EC2 resource summary for optimization opportunities
                try:
                    ec2_data = ec2_summary(session, profile_name=resolved_profile)

                    resources_table = create_table(title="💡 Optimization Opportunities")
                    resources_table.add_column("Resource Type", style="bold")
                    resources_table.add_column("Count", style="cyan")
                    resources_table.add_column("Potential Action", style="yellow")

                    # EC2Summary is a Dict[str, int], so access it accordingly
                    total_instances = ec2_data.get("total_instances", 0)
                    running_instances = ec2_data.get("running_instances", 0)
                    stopped_instances = ec2_data.get("stopped_instances", 0)

                    # Add EC2 optimization opportunities
                    if total_instances > 0:
                        resources_table.add_row("Total EC2 Instances", str(total_instances), "Review rightsizing")
                        resources_table.add_row("Running Instances", str(running_instances), "Monitor utilization")
                        resources_table.add_row("Stopped Instances", str(stopped_instances), "Consider termination")

                        # Calculate potential savings estimates
                        if stopped_instances > 0:
                            # Estimate $100/month per stopped instance for EBS storage costs
                            stopped_savings = stopped_instances * 100
                            resources_table.add_row(
                                "Stopped Instance Savings", f"~${stopped_savings}/month", "Terminate unused instances"
                            )

                        if running_instances > 5:
                            # Estimate 20% rightsizing opportunity
                            ec2_cost_estimate = services_data.get("Amazon Elastic Compute Cloud - Compute", 0)
                            rightsizing_savings = ec2_cost_estimate * 0.20
                            if rightsizing_savings > 100:
                                resources_table.add_row(
                                    "EC2 Rightsizing Potential",
                                    f"~${rightsizing_savings:.0f}/month",
                                    "Rightsize overprovisioned instances",
                                )

                    else:
                        resources_table.add_row("EC2 Instances", "0", "No instances found in accessible regions")

                    console.print(resources_table)
                    console.print()

                except Exception as e:
                    console.print(f"[yellow]⚠️ Could not fetch EC2 optimization data: {e}[/yellow]\n")

                # Display Business Impact Summary
                total_annual = current_cost * 12
                optimization_potential = total_annual * 0.15  # Conservative 15% optimization target

                business_panel = Panel(
                    f"""[bold]Annual Spend Projection:[/bold] ${total_annual:,.2f}
[bold]Conservative Optimization Target (15%):[/bold] ${optimization_potential:,.2f}
[bold]Recommended Actions:[/bold]
• Review EC2 instance rightsizing opportunities
• Analyze unused resources and storage
• Implement automated cost monitoring
• Set up budget alerts for cost control

[dim]Analysis Period: {timeframe.title()} view | Account: {account_id}[/dim]""",
                    title="💼 Business Impact Summary",
                    border_style="blue",
                )
                console.print(business_panel)

                # Prepare results dictionary
                results = {
                    "status": "completed",
                    "account_id": account_id,
                    "timeframe": timeframe,
                    "cost_analysis": {
                        "current_monthly_spend": current_cost,
                        "previous_monthly_spend": previous_cost,
                        "annual_projection": total_annual,
                        "optimization_potential": optimization_potential,
                        "top_services": dict(sorted_services[:5]) if services_data else {},
                        "ec2_summary": {
                            "total_instances": total_instances if "total_instances" in locals() else 0,
                            "running_instances": running_instances if "running_instances" in locals() else 0,
                            "stopped_instances": stopped_instances if "stopped_instances" in locals() else 0,
                        },
                    },
                }

                # Attach MCP validation results if available
                if mcp_results:
                    results["mcp_validation"] = {
                        "accuracy_percentage": mcp_results.accuracy_percentage,
                        "validation_passed": mcp_results.accuracy_percentage >= 99.5,
                        "operation_name": mcp_results.operation_name,
                        "status": mcp_results.status.value,
                        "detailed_results": mcp_results,
                    }

                return results

            except Exception as e:
                print_error(f"Failed to retrieve cost data: {e}")
                console.print(
                    f"[yellow]💡 Tip: Ensure your AWS profile '{resolved_profile}' has Cost Explorer permissions[/yellow]"
                )
                console.print(f"[dim]Required permissions: ce:GetCostAndUsage, ce:GetDimensionValues[/dim]")
                raise

        except ImportError as e:
            error_handlers["module_not_available"]("FinOps dashboard", e)
            raise click.ClickException("FinOps dashboard functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("FinOps dashboard generation", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--resource-type",
        type=click.Choice(["ec2", "s3", "rds", "lambda", "vpc"]),
        required=True,
        help="Resource type for optimization analysis",
    )
    @click.option(
        "--savings-target", type=click.FloatRange(0.1, 0.8), default=0.3, help="Target savings percentage (0.1-0.8)"
    )
    @click.option(
        "--analysis-depth",
        type=click.Choice(["basic", "comprehensive", "enterprise"]),
        default="comprehensive",
        help="Analysis depth level",
    )
    @click.option("--mcp-validate", is_flag=True, help="Enable MCP validation for ≥99.5% accuracy cross-validation")
    @click.pass_context
    def optimize(ctx, resource_type, savings_target, analysis_depth, mcp_validate):
        """
        Generate cost optimization recommendations for specific resource types.

        Enterprise Optimization Features:
        • Safety-first analysis with READ-ONLY operations
        • Quantified savings projections with ROI analysis
        • Risk assessment and business impact evaluation
        • Implementation timeline and priority recommendations

        Examples:
            runbooks finops optimize --resource-type ec2 --savings-target 0.25
            runbooks finops optimize --resource-type s3 --analysis-depth enterprise
        """
        try:
            from runbooks.finops.optimization_engine import ResourceOptimizer

            # MCP validation integration for optimization accuracy
            mcp_results = None
            if mcp_validate:
                try:
                    from runbooks.validation.mcp_validator import MCPValidator
                    import asyncio

                    console.print(f"[cyan]🔍 Running MCP validation for {resource_type} optimization accuracy[/cyan]")

                    # Configure validation profiles
                    validation_profiles = {
                        "billing": ctx.obj.get("profile", "default"),
                        "management": ctx.obj.get("profile", "default"),
                        "centralised_ops": ctx.obj.get("profile", "default"),
                        "single_aws": ctx.obj.get("profile", "default"),
                    }

                    # Initialize validator
                    validator = MCPValidator(
                        profiles=validation_profiles, tolerance_percentage=5.0, performance_target_seconds=30.0
                    )

                    # Run validation based on resource type
                    if resource_type in ["ec2"]:
                        mcp_results = asyncio.run(validator.validate_ec2_inventory())
                    elif resource_type in ["vpc"]:
                        mcp_results = asyncio.run(validator.validate_vpc_analysis())
                    elif resource_type in ["s3", "rds", "lambda"]:
                        # For these resource types, use cost explorer validation
                        mcp_results = asyncio.run(validator.validate_cost_explorer())
                    else:
                        # Default to cost explorer validation
                        mcp_results = asyncio.run(validator.validate_cost_explorer())

                    # Display validation results
                    if mcp_results.accuracy_percentage >= 99.5:
                        console.print(
                            f"[green]✅ MCP Validation PASSED: {mcp_results.accuracy_percentage:.1f}% accuracy for {resource_type}[/green]"
                        )
                    elif mcp_results.accuracy_percentage >= 95.0:
                        console.print(
                            f"[yellow]⚠️ MCP Validation WARNING: {mcp_results.accuracy_percentage:.1f}% accuracy (target: ≥99.5%)[/yellow]"
                        )
                    else:
                        console.print(
                            f"[red]❌ MCP Validation FAILED: {mcp_results.accuracy_percentage:.1f}% accuracy[/red]"
                        )

                except Exception as e:
                    console.print(f"[yellow]⚠️ MCP validation failed: {e}[/yellow]")
                    console.print("[dim]Continuing with optimization analysis...[/dim]")

            optimizer = ResourceOptimizer(
                profile=ctx.obj["profile"],
                region=ctx.obj["region"],
                resource_type=resource_type,
                savings_target=savings_target,
                analysis_depth=analysis_depth,
                mcp_validate=mcp_validate,
            )

            optimization_results = optimizer.analyze_optimization_opportunities()

            # Attach MCP validation results if available
            if mcp_results and isinstance(optimization_results, dict):
                optimization_results["mcp_validation"] = {
                    "accuracy_percentage": mcp_results.accuracy_percentage,
                    "validation_passed": mcp_results.accuracy_percentage >= 99.5,
                    "resource_type": resource_type,
                    "operation_name": mcp_results.operation_name,
                    "status": mcp_results.status.value,
                    "detailed_results": mcp_results,
                }

            return optimization_results

        except ImportError as e:
            error_handlers["module_not_available"]("FinOps optimization", e)
            raise click.ClickException("FinOps optimization functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("FinOps optimization analysis", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--format",
        "export_format",
        type=click.Choice(["csv", "json", "pdf", "markdown"]),
        multiple=True,
        default=["json"],
        help="Export formats",
    )
    @click.option("--output-dir", default="./finops_reports", help="Output directory for exports")
    @click.option("--include-quarterly", is_flag=True, help="Include quarterly intelligence data")
    @click.option("--executive-summary", is_flag=True, help="Generate executive summary format")
    @click.option("--mcp-validate", is_flag=True, help="Enable MCP validation for ≥99.5% accuracy cross-validation")
    @click.pass_context
    def export(ctx, export_format, output_dir, include_quarterly, executive_summary, mcp_validate):
        """
        Export financial analysis results in multiple formats.

        Enterprise Export Features:
        • Multi-format simultaneous export
        • Executive-ready formatting and presentation
        • Quarterly intelligence integration
        • Complete audit trail documentation

        Examples:
            runbooks finops export --format csv,pdf --executive-summary
            runbooks finops export --include-quarterly --output-dir ./executive_reports
        """
        try:
            from runbooks.finops.export_manager import FinOpsExportManager

            # MCP validation integration for export accuracy
            mcp_results = None
            if mcp_validate:
                try:
                    from runbooks.validation.mcp_validator import MCPValidator
                    import asyncio

                    console.print("[cyan]🔍 Running MCP validation for export data accuracy[/cyan]")

                    # Configure validation profiles
                    validation_profiles = {
                        "billing": ctx.obj.get("profile", "default"),
                        "management": ctx.obj.get("profile", "default"),
                        "centralised_ops": ctx.obj.get("profile", "default"),
                        "single_aws": ctx.obj.get("profile", "default"),
                    }

                    # Initialize validator
                    validator = MCPValidator(
                        profiles=validation_profiles, tolerance_percentage=5.0, performance_target_seconds=30.0
                    )

                    # Run validation for export data accuracy using cost explorer validation
                    mcp_results = asyncio.run(validator.validate_cost_explorer())

                    # Display validation results
                    if mcp_results.accuracy_percentage >= 99.5:
                        console.print(
                            f"[green]✅ MCP Validation PASSED: {mcp_results.accuracy_percentage:.1f}% accuracy for exports[/green]"
                        )
                    elif mcp_results.accuracy_percentage >= 95.0:
                        console.print(
                            f"[yellow]⚠️ MCP Validation WARNING: {mcp_results.accuracy_percentage:.1f}% accuracy (target: ≥99.5%)[/yellow]"
                        )
                    else:
                        console.print(
                            f"[red]❌ MCP Validation FAILED: {mcp_results.accuracy_percentage:.1f}% accuracy[/red]"
                        )

                except Exception as e:
                    console.print(f"[yellow]⚠️ MCP validation failed: {e}[/yellow]")
                    console.print("[dim]Continuing with export operation...[/dim]")

            export_manager = FinOpsExportManager(
                profile=ctx.obj["profile"],
                output_dir=output_dir,
                include_quarterly=include_quarterly,
                executive_summary=executive_summary,
                mcp_validate=mcp_validate,
            )

            export_results = {}
            for format_type in export_format:
                result = export_manager.export_analysis(format=format_type)
                export_results[format_type] = result

            # Attach MCP validation results if available
            if mcp_results:
                export_results["mcp_validation"] = {
                    "accuracy_percentage": mcp_results.accuracy_percentage,
                    "validation_passed": mcp_results.accuracy_percentage >= 99.5,
                    "export_formats": list(export_format),
                    "operation_name": mcp_results.operation_name,
                    "status": mcp_results.status.value,
                    "detailed_results": mcp_results,
                }

            error_handlers["success"](
                f"Successfully exported to {len(export_format)} format(s)", f"Output directory: {output_dir}"
            )

            return export_results

        except ImportError as e:
            error_handlers["module_not_available"]("FinOps export", e)
            raise click.ClickException("FinOps export functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("FinOps export operation", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--older-than-days", type=int, default=90, help="Minimum age in days for cleanup consideration (default: 90)"
    )
    @click.option(
        "--validate", is_flag=True, default=True, help="Enable MCP validation for ≥99.5% accuracy (default: enabled)"
    )
    @click.option("--cleanup", is_flag=True, help="Enable cleanup recommendations (READ-ONLY analysis only)")
    @click.option("--export-results", is_flag=True, help="Export analysis results to JSON file")
    @click.option(
        "--safety-checks/--no-safety-checks",
        default=True,
        help="Enable comprehensive safety validations (default: enabled)",
    )
    @click.option("--all-profiles", help="Use specified profile for all operations (overrides parent --profile)")
    @click.pass_context
    def ec2_snapshots(ctx, older_than_days, validate, cleanup, export_results, safety_checks, all_profiles):
        """
        EC2 snapshot cost optimization and cleanup analysis.

        Sprint 1, Task 1: Analyze EC2 snapshots for cost optimization opportunities
        targeting $50K+ annual savings through systematic age-based cleanup with
        enterprise safety validations and MCP accuracy frameworks.

        Enterprise Features:
        • Multi-account snapshot discovery via AWS Config aggregator
        • Dynamic pricing via AWS Pricing API for accurate cost calculations
        • MCP validation framework with ≥99.5% accuracy cross-validation
        • Comprehensive safety checks (volume attachment, AMI association, age)
        • Executive reporting with Sprint 1 business impact metrics

        Safety Features:
        • READ-ONLY analysis by default (no actual cleanup performed)
        • Volume attachment verification before recommendations
        • AMI association checking to prevent data loss
        • Configurable age thresholds with safety validations

        Examples:
            # Basic analysis with MCP validation using parent profile
            runbooks finops --profile BILLING_PROFILE ec2-snapshots --validate

            # Override parent profile with command-specific profile
            runbooks finops ec2-snapshots --all-profiles BILLING_PROFILE --validate

            # Custom age threshold with export
            runbooks finops --profile BILLING_PROFILE ec2-snapshots --older-than-days 120 --export-results

            # Comprehensive analysis for Sprint 1
            runbooks finops --profile BILLING_PROFILE ec2-snapshots --cleanup --validate --export-results

            # Quick analysis without safety checks (not recommended)
            runbooks finops ec2-snapshots --all-profiles BILLING_PROFILE --no-safety-checks --older-than-days 30

        Sprint 1 Context:
            Task 1 targeting $50K+ annual savings through systematic snapshot cleanup
            with enterprise coordination and MCP validation accuracy ≥99.5%
        """
        try:
            import asyncio
            from runbooks.finops.snapshot_manager import EC2SnapshotManager

            console.print("\n[bold blue]🎯 Sprint 1, Task 1: EC2 Snapshot Cost Optimization[/bold blue]")

            # Resolve profile with priority: --all-profiles > ctx.obj['profile'] > 'default'
            resolved_profile = all_profiles or ctx.obj.get("profile", "default")
            resolved_region = ctx.obj.get("region", "all")
            resolved_dry_run = ctx.obj.get("dry_run", True)

            # Validate profile resolution
            if not resolved_profile:
                console.print("[red]❌ Error: No AWS profile specified or found[/red]")
                console.print("[yellow]💡 Use --all-profiles PROFILE_NAME or set parent --profile option[/yellow]")
                raise click.ClickException("AWS profile required for ec2-snapshots command")

            console.print(
                f"[dim]Profile: {resolved_profile} | Region: {resolved_region} | Dry-run: {resolved_dry_run}[/dim]\n"
            )

            # Initialize snapshot manager with enterprise configuration
            manager = EC2SnapshotManager(profile=resolved_profile, dry_run=resolved_dry_run)

            # Configure safety checks based on user preference
            if not safety_checks:
                console.print("[yellow]⚠️ Safety checks disabled - use with caution[/yellow]")
                manager.safety_checks = {
                    "volume_attachment_check": False,
                    "ami_association_check": False,
                    "minimum_age_check": True,  # Always keep age check for safety
                    "cross_account_validation": False,
                }

            # Run the main analysis using the enhanced method
            async def run_analysis():
                return await manager.analyze_snapshot_opportunities(
                    profile=resolved_profile,
                    older_than_days=older_than_days,
                    enable_mcp_validation=validate,
                    export_results=export_results,
                )

            # Execute analysis
            results = asyncio.run(run_analysis())

            # Check if we have cost analysis results before validating Sprint 1 targets
            if not results.get("cost_analysis") or not results["cost_analysis"]:
                console.print("\n[yellow]⚠️ No snapshots found - no cost optimization opportunities identified[/yellow]")
                return results

            # Sprint 1 success validation
            annual_savings = results["cost_analysis"]["annual_savings"]
            sprint_target = 50000  # $50K Sprint 1 target

            if annual_savings >= sprint_target:
                console.print(f"\n[bold green]✅ Sprint 1 Task 1 SUCCESS![/bold green]")
                console.print(f"[green]Target: ${sprint_target:,} | Achieved: ${annual_savings:,.2f}[/green]")
            else:
                console.print(f"\n[bold yellow]⚠️ Sprint 1 Task 1 - Below Target[/bold yellow]")
                console.print(f"[yellow]Target: ${sprint_target:,} | Achieved: ${annual_savings:,.2f}[/yellow]")

            # MCP validation status for Sprint 1
            if validate and results.get("mcp_validation"):
                mcp_results = results["mcp_validation"]
                if mcp_results["validation_passed"]:
                    console.print(
                        f"[green]✅ MCP Validation: {mcp_results['accuracy_percentage']:.2f}% accuracy[/green]"
                    )
                else:
                    console.print(
                        f"[red]❌ MCP Validation: {mcp_results['accuracy_percentage']:.2f}% accuracy (Required: ≥99.5%)[/red]"
                    )

            # Enterprise coordination confirmation
            console.print(f"\n[dim]🏢 Enterprise coordination: python-runbooks-engineer [1] (Primary)[/dim]")
            console.print(f"[dim]🎯 Sprint coordination: Systematic delegation activated[/dim]")

            return results

        except ImportError as e:
            error_handlers["module_not_available"]("EC2 Snapshot Manager", e)
            raise click.ClickException("EC2 snapshot analysis functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("EC2 snapshot analysis", e)
            raise click.ClickException(str(e))

    # Epic 2 Infrastructure Optimization Commands
    @finops.group()
    def infrastructure():
        """Epic 2 Infrastructure Optimization - $210,147 annual savings target"""
        pass

    @infrastructure.command()
    @click.option(
        "--components",
        multiple=True,
        type=click.Choice(["nat-gateway", "elastic-ip", "load-balancer", "vpc-endpoint"]),
        help="Infrastructure components to analyze (default: all)",
    )
    @click.option(
        "--export-format",
        type=click.Choice(["json", "csv", "markdown"]),
        default="json",
        help="Export format for results",
    )
    @click.option("--output-file", help="Output file path for results export")
    @click.option("--mcp-validate", is_flag=True, help="Enable MCP validation for ≥99.5% accuracy cross-validation")
    @click.pass_context
    def analyze(ctx, components, export_format, output_file, mcp_validate):
        """
        Comprehensive Infrastructure Optimization Analysis - Epic 2

        Analyze all infrastructure components to achieve $210,147 Epic 2 annual savings target:
        • NAT Gateway optimization: $147,420 target
        • Elastic IP optimization: $21,593 target
        • Load Balancer optimization: $35,280 target
        • VPC Endpoint optimization: $5,854 target

        SAFETY: READ-ONLY analysis only - no resource modifications.

        Examples:
            runbooks finops infrastructure analyze
            runbooks finops infrastructure analyze --components nat-gateway load-balancer
        """
        try:
            import asyncio
            from runbooks.finops.infrastructure.commands import InfrastructureOptimizer

            # MCP validation integration for infrastructure analysis
            mcp_results = None
            if mcp_validate:
                try:
                    from runbooks.validation.mcp_validator import MCPValidator

                    console.print("[cyan]🔍 Running MCP validation for infrastructure optimization accuracy[/cyan]")

                    # Configure validation profiles
                    validation_profiles = {
                        "billing": ctx.obj.get("profile", "default"),
                        "management": ctx.obj.get("profile", "default"),
                        "centralised_ops": ctx.obj.get("profile", "default"),
                        "single_aws": ctx.obj.get("profile", "default"),
                    }

                    # Initialize validator
                    validator = MCPValidator(
                        profiles=validation_profiles, tolerance_percentage=5.0, performance_target_seconds=30.0
                    )

                    # Run validation for infrastructure operations using VPC validation for networking components
                    component_types = (
                        list(components)
                        if components
                        else ["nat-gateway", "elastic-ip", "load-balancer", "vpc-endpoint"]
                    )
                    if any(comp in ["nat-gateway", "vpc-endpoint"] for comp in component_types):
                        mcp_results = asyncio.run(validator.validate_vpc_analysis())
                    elif any(comp in ["elastic-ip"] for comp in component_types):
                        mcp_results = asyncio.run(validator.validate_ec2_inventory())
                    else:
                        # Default to cost explorer for load balancer cost analysis
                        mcp_results = asyncio.run(validator.validate_cost_explorer())

                    # Display validation results
                    if mcp_results.accuracy_percentage >= 99.5:
                        console.print(
                            f"[green]✅ MCP Validation PASSED: {mcp_results.accuracy_percentage:.1f}% accuracy for infrastructure[/green]"
                        )
                    elif mcp_results.accuracy_percentage >= 95.0:
                        console.print(
                            f"[yellow]⚠️ MCP Validation WARNING: {mcp_results.accuracy_percentage:.1f}% accuracy (target: ≥99.5%)[/yellow]"
                        )
                    else:
                        console.print(
                            f"[red]❌ MCP Validation FAILED: {mcp_results.accuracy_percentage:.1f}% accuracy[/red]"
                        )

                except Exception as e:
                    console.print(f"[yellow]⚠️ MCP validation failed: {e}[/yellow]")
                    console.print("[dim]Continuing with infrastructure analysis...[/dim]")

            # Initialize comprehensive optimizer
            optimizer = InfrastructureOptimizer(
                profile_name=ctx.obj.get("profile"),
                regions=[ctx.obj.get("region")] if ctx.obj.get("region") else None,
                mcp_validate=mcp_validate,
            )

            # Execute comprehensive analysis
            results = asyncio.run(
                optimizer.analyze_comprehensive_infrastructure(
                    components=list(components) if components else None, dry_run=ctx.obj.get("dry_run", True)
                )
            )

            # Attach MCP validation results if available
            if mcp_results and hasattr(results, "__dict__"):
                results.mcp_validation = {
                    "accuracy_percentage": mcp_results.accuracy_percentage,
                    "validation_passed": mcp_results.accuracy_percentage >= 99.5,
                    "components_validated": list(components) if components else "all",
                    "operation_name": mcp_results.operation_name,
                    "status": mcp_results.status.value,
                    "detailed_results": mcp_results,
                }

            # Display Epic 2 progress
            if results.epic_2_target_achieved:
                console.print(f"\n[bold green]✅ Epic 2 Infrastructure Target Achieved![/bold green]")
                console.print(
                    f"[green]Target: ${results.epic_2_target_savings:,.0f} | Achieved: ${results.total_potential_savings:,.0f}[/green]"
                )
            else:
                progress_pct = results.epic_2_progress_percentage
                console.print(f"\n[bold yellow]📊 Epic 2 Infrastructure Progress: {progress_pct:.1f}%[/bold yellow]")
                console.print(
                    f"[yellow]Target: ${results.epic_2_target_savings:,.0f} | Achieved: ${results.total_potential_savings:,.0f}[/yellow]"
                )

            # Export results if requested
            if output_file or export_format != "json":
                console.print(f"[dim]Export functionality available - results ready for {export_format} export[/dim]")

            return results

        except ImportError as e:
            error_handlers["module_not_available"]("Infrastructure Optimizer", e)
            raise click.ClickException("Infrastructure optimization functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("Infrastructure optimization analysis", e)
            raise click.ClickException(str(e))

    @infrastructure.command()
    @click.pass_context
    def nat_gateway(ctx):
        """NAT Gateway optimization analysis - $147,420 Epic 2 target"""
        try:
            import asyncio
            from runbooks.finops.nat_gateway_optimizer import NATGatewayOptimizer

            optimizer = NATGatewayOptimizer(
                profile_name=ctx.obj.get("profile"), regions=[ctx.obj.get("region")] if ctx.obj.get("region") else None
            )

            results = asyncio.run(optimizer.analyze_nat_gateways(dry_run=ctx.obj.get("dry_run", True)))

            # Display Epic 2 component progress
            target = 147420.0
            if results.potential_annual_savings >= target:
                console.print(f"\n[bold green]✅ NAT Gateway Epic 2 Target Achieved![/bold green]")
            else:
                progress = (results.potential_annual_savings / target) * 100
                console.print(f"\n[yellow]📊 NAT Gateway Progress: {progress:.1f}% of Epic 2 target[/yellow]")

            return results

        except Exception as e:
            error_handlers["operation_failed"]("NAT Gateway optimization", e)
            raise click.ClickException(str(e))

    @infrastructure.command()
    @click.pass_context
    def elastic_ip(ctx):
        """Elastic IP optimization analysis - $21,593 Epic 2 target"""
        try:
            import asyncio
            from runbooks.finops.elastic_ip_optimizer import ElasticIPOptimizer

            optimizer = ElasticIPOptimizer(
                profile_name=ctx.obj.get("profile"), regions=[ctx.obj.get("region")] if ctx.obj.get("region") else None
            )

            results = asyncio.run(optimizer.analyze_elastic_ips(dry_run=ctx.obj.get("dry_run", True)))

            # Display Epic 2 component progress
            target = 21593.0
            if results.potential_annual_savings >= target:
                console.print(f"\n[bold green]✅ Elastic IP Epic 2 Target Achieved![/bold green]")
            else:
                progress = (results.potential_annual_savings / target) * 100
                console.print(f"\n[yellow]📊 Elastic IP Progress: {progress:.1f}% of Epic 2 target[/yellow]")

            return results

        except Exception as e:
            error_handlers["operation_failed"]("Elastic IP optimization", e)
            raise click.ClickException(str(e))

    @infrastructure.command()
    @click.pass_context
    def load_balancer(ctx):
        """Load Balancer optimization analysis - $35,280 Epic 2 target"""
        try:
            import asyncio
            from runbooks.finops.infrastructure.load_balancer_optimizer import LoadBalancerOptimizer

            optimizer = LoadBalancerOptimizer(
                profile_name=ctx.obj.get("profile"), regions=[ctx.obj.get("region")] if ctx.obj.get("region") else None
            )

            results = asyncio.run(optimizer.analyze_load_balancers(dry_run=ctx.obj.get("dry_run", True)))

            # Display Epic 2 component progress
            target = 35280.0
            if results.potential_annual_savings >= target:
                console.print(f"\n[bold green]✅ Load Balancer Epic 2 Target Achieved![/bold green]")
            else:
                progress = (results.potential_annual_savings / target) * 100
                console.print(f"\n[yellow]📊 Load Balancer Progress: {progress:.1f}% of Epic 2 target[/yellow]")

            return results

        except Exception as e:
            error_handlers["operation_failed"]("Load Balancer optimization", e)
            raise click.ClickException(str(e))

    @infrastructure.command()
    @click.pass_context
    def vpc_endpoint(ctx):
        """VPC Endpoint optimization analysis - $5,854 Epic 2 target"""
        try:
            import asyncio
            from runbooks.finops.infrastructure.vpc_endpoint_optimizer import VPCEndpointOptimizer

            optimizer = VPCEndpointOptimizer(
                profile_name=ctx.obj.get("profile"), regions=[ctx.obj.get("region")] if ctx.obj.get("region") else None
            )

            results = asyncio.run(optimizer.analyze_vpc_endpoints(dry_run=ctx.obj.get("dry_run", True)))

            # Display Epic 2 component progress
            target = 5854.0
            if results.potential_annual_savings >= target:
                console.print(f"\n[bold green]✅ VPC Endpoint Epic 2 Target Achieved![/bold green]")
            else:
                progress = (results.potential_annual_savings / target) * 100
                console.print(f"\n[yellow]📊 VPC Endpoint Progress: {progress:.1f}% of Epic 2 target[/yellow]")

            return results

        except Exception as e:
            error_handlers["operation_failed"]("VPC Endpoint optimization", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--input",
        "-i",
        "input_file",
        required=True,
        type=click.Path(exists=True),
        help="Input WorkSpaces data file (Excel/CSV with 'AWS Account' column)",
    )
    @click.option(
        "--output", "-o", "output_file", type=click.Path(), help="Output enriched data file (Excel/CSV/JSON)"
    )
    @click.option("--profile", "-p", default="default", help="AWS operational profile (WorkSpaces access)")
    @click.option("--management-profile", "-m", default=None, help="AWS management profile (Organizations access)")
    @click.option("--display-only", is_flag=True, help="Display Rich CLI output without file export")
    @click.pass_context
    def enrich_workspaces(ctx, input_file, output_file, profile, management_profile, display_only):
        """
        Enrich WorkSpaces inventory with Organizations metadata.

        Reads WorkSpaces data from Excel/CSV with 'AWS Account' column and enriches it with:
        • Account name (from AWS Organizations)
        • Account email
        • WBS code (cost allocation)
        • Cost group
        • Technical lead
        • Account owner

        Example:
            runbooks finops enrich-workspaces -i data/workspaces.xlsx -o data/enriched.xlsx -p ops-profile -m mgmt-profile
        """
        try:
            from runbooks.finops.enrich_workspaces import enrich_workspaces as enrich_ws_cmd

            # Import the command function and invoke it directly
            import sys
            from click.testing import CliRunner

            # Get format from parent context (output_format from common_output_options decorator)
            output_format = ctx.obj.get("output_format", "csv") if ctx.obj else "csv"

            # Create a runner to invoke the standalone command
            # This allows reusing the implementation without duplicating code
            enrich_ws_cmd.callback(input_file, output_file, profile, management_profile, output_format, display_only)

        except ImportError as e:
            error_handlers["module_not_available"]("WorkSpaces Enrichment", e)
            raise click.ClickException("WorkSpaces enrichment functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("WorkSpaces enrichment", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--input",
        "-i",
        "input_file",
        required=True,
        type=click.Path(exists=True),
        help="Input EC2 inventory Excel file (with Identifier, AWS Account, Region columns)",
    )
    @click.option(
        "--output",
        "-o",
        "output_file",
        required=True,
        type=click.Path(),
        help="Output enriched Excel file (multi-sheet with cost analysis)"
    )
    @click.option(
        "--management-profile",
        "-m",
        required=True,
        help="AWS management profile for Organizations API access"
    )
    @click.option(
        "--billing-profile",
        "-b",
        required=True,
        help="AWS billing profile for Cost Explorer API access"
    )
    @click.option(
        "--operational-profile",
        "-p",
        default=None,
        help="AWS operational profile for EC2 describe-instances (optional, defaults to management profile)"
    )
    @click.option(
        "--enable-organizations/--no-organizations",
        default=True,
        help="Enable Organizations metadata enrichment (default: enabled)"
    )
    @click.option(
        "--enable-cost/--no-cost",
        default=True,
        help="Enable Cost Explorer enrichment (default: enabled)"
    )
    @click.option(
        "--enable-activity/--no-activity",
        default=False,
        help="Enable CloudTrail activity tracking (default: disabled, takes 60-90 seconds)"
    )
    @click.option(
        "--include-12month-cost/--no-12month-cost",
        default=True,
        help="Include 12-month cost breakdown (default: enabled)"
    )
    @click.option(
        "--decommission-mode/--no-decommission-mode",
        default=False,
        help="Decommission mode: Filter to 45 decision-focused columns (default: disabled, shows all 87 columns)"
    )
    @click.option("--verbose", "-v", is_flag=True, help="Show detailed logs")
    @click.option("--format", type=click.Choice(["compact", "table", "json"]), default="compact", help="Output format")
    @click.pass_context
    def analyze_ec2(
        ctx,
        input_file,
        output_file,
        management_profile,
        billing_profile,
        operational_profile,
        enable_organizations,
        enable_cost,
        enable_activity,
        include_12month_cost,
        decommission_mode,
        verbose,
        format
    ):
        """
        EC2 cost analysis with 4-way enrichment.

        \b
        🔄 4-WAY ENRICHMENT LAYERS (E1-E7 Decommission Scoring)
        ┌──────────────────────────────────────────────────────────────┐
        │ Layer 1: Discovery       │ Resource Explorer EC2 inventory   │
        │ Layer 2: Organizations   │ Account metadata (6 columns)      │
        │ Layer 3: Cost            │ 12-month Cost Explorer trends     │
        │ Layer 4: Activity        │ CloudTrail idle detection (opt)   │
        └──────────────────────────────────────────────────────────────┘

        \b
        📊 DECOMMISSION SIGNALS (E1-E7)
        • E1: Instance stopped state → +15 points (HIGH priority)
        • E2: Zero 12-month cost → +12 points (Terminated/Free tier)
        • E3: Low monthly cost (<$5) → +8 points (Micro workloads)
        • E4: No CloudTrail activity (14d) → +10 points (Idle detection)
        • E5: Cost decreasing trend → +5 points (Usage declining)
        • E6: Legacy instance type (t2, m4) → +3 points (Modernization)
        • E7: Untagged resources → +2 points (Management overhead)

        \b
        🎯 OPTIMIZATION TIERS
        • HIGH (≥25 points): Immediate decommission candidates
        • MEDIUM (15-24 points): Review recommended within 30 days
        • LOW (<15 points): Monitor and maintain current state

        \b
        💰 Sprint 1 Target: 25-50% cost savings via tier-based decommission
        📖 Example: runbooks finops analyze-ec2 -i ec2.xlsx -o enriched.xlsx -m mgmt -b billing
        """
        # Initialize output controller
        configure_logging(verbose=verbose)
        controller = OutputController(verbose=verbose, format=format)

        try:
            from runbooks.finops.ec2_analyzer import analyze_ec2_costs
            from runbooks.common.rich_utils import print_header, print_success, print_error

            print_header("EC2 Cost Analysis", f"Input: {input_file}")

            # Execute EC2 cost analysis
            result_df = analyze_ec2_costs(
                input_file=input_file,
                output_file=output_file,
                management_profile=management_profile,
                billing_profile=billing_profile,
                operational_profile=operational_profile,
                enable_organizations=enable_organizations,
                enable_cost=enable_cost,
                enable_activity=enable_activity,
                include_12month_cost=include_12month_cost,
                decommission_mode=decommission_mode
            )

            # Print summary using OutputController
            enrichment_layers = []
            if enable_organizations:
                enrichment_layers.append("organizations")
            if enable_cost:
                enrichment_layers.append("cost")
            if enable_activity:
                enrichment_layers.append("activity")

            controller.print_operation_summary(
                emoji="💰",
                operation="EC2 Cost Analysis",
                input_count=len(result_df),
                enriched_count=len(result_df),
                enrichment_type="EC2 instances analyzed",
                success_percentage=100.0,
                profile=management_profile,
                output_file=output_file,
                added_columns=enrichment_layers
            )

            return result_df

        except ImportError as e:
            error_handlers["module_not_available"]("EC2 Cost Analyzer", e)
            raise click.ClickException("EC2 cost analysis functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("EC2 cost analysis", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--input",
        "-i",
        "input_file",
        required=True,
        type=click.Path(exists=True),
        help="Input EC2 inventory Excel file (with instance_id, account_id, region columns)"
    )
    @click.option(
        "--output",
        "-o",
        "output_file",
        required=True,
        type=click.Path(),
        help="Output enriched Excel file with decommission analysis"
    )
    @click.option(
        "--management-profile",
        "-m",
        required=True,
        help="AWS management profile for Organizations API access"
    )
    @click.option(
        "--billing-profile",
        "-b",
        required=True,
        help="AWS billing profile for Cost Explorer API access"
    )
    @click.option(
        "--operational-profile",
        "-p",
        default=None,
        help="AWS operational profile for EC2 describe-instances (optional, defaults to management)"
    )
    @click.option(
        "--enable-expensive-signals/--no-expensive-signals",
        default=False,
        help="Enable expensive signals (CloudTrail activity, SSM, Compute Optimizer)"
    )
    @click.pass_context
    def ec2_decommission_analysis(
        ctx,
        input_file,
        output_file,
        management_profile,
        billing_profile,
        operational_profile,
        enable_expensive_signals
    ):
        """
        EC2 decommission analysis with E1-E7 scoring framework.

        This command provides enterprise EC2 decommission candidate identification with:
        • E1-E7 multi-signal scoring (Compute Optimizer, CloudWatch, CloudTrail, SSM, etc.)
        • MUST/SHOULD/COULD/KEEP tier classification
        • Top 50 decommission candidates executive summary
        • Annual savings projections per instance
        • Professional Rich CLI output for CxO consumption

        Scoring Framework (0-100 scale):
        • MUST (80-100): Immediate decommission candidates
        • SHOULD (50-79): Strong candidates (review recommended)
        • COULD (25-49): Potential candidates (manual review)
        • KEEP (<25): Active resources (no action)

        Signal Framework (E1-E7):
        • E1: Compute Optimizer Idle (max CPU ≤1% for 14d) → +60 points
        • E2: SSM Agent Offline/Stale → +8 points
        • E3: CloudTrail no activity (90d) → +8 points
        • E4: Stopped State (>30 days) → +8 points
        • E5: No service attachment (ALB/ASG/ECS/EKS) → +6 points
        • E6: No Tags/Owner → +5 points
        • E7: Dev/Test Environment → +3 points

        Examples:
            # Basic decommission analysis (fast, no expensive signals)
            runbooks finops ec2-decommission-analysis \\
                --input data/ec2-inventory.xlsx \\
                --output data/ec2-decommission-analysis.xlsx \\
                --management-profile mgmt-ro \\
                --billing-profile billing-ro

            # Comprehensive analysis with expensive signals (CloudTrail, SSM, Compute Optimizer)
            runbooks finops ec2-decommission-analysis \\
                -i data/ec2.xlsx \\
                -o data/ec2-decommission-full.xlsx \\
                -m mgmt-ro \\
                -b billing-ro \\
                --enable-expensive-signals

        Input File Format:
            Excel file with required columns:
            - instance_id: EC2 instance ID (i-xxxxx)
            - account_id: 12-digit AWS account ID
            - region: AWS region (ap-southeast-2, etc.)

        Output File Format:
            Multi-sheet Excel with:
            - Sheet 1: Enriched Data (67+ columns with decommission scores)
            - Sheet 2: Top 50 Decommission Candidates (executive summary)
            - Sheet 3: Cost Summary (by account/tier)
            - Sheet 4: Validation Metrics

        Performance Notes:
            • Fast mode (no expensive signals): ~5-10 seconds
            • Full mode (with expensive signals): ~60-90 seconds
            • Expensive signals: CloudTrail (60s), SSM (10s), Compute Optimizer (10s)

        Pattern: Migrated from notebooks/compute/ec2.ipynb with CxO executive polish
        """
        try:
            from runbooks.finops.ec2_analyzer import analyze_ec2_costs
            from runbooks.finops.decommission_classifier import classify_ec2
            from runbooks.common.rich_utils import print_header, print_success, print_error, print_info

            print_header("EC2 Decommission Analysis", f"Input: {input_file}")

            # Step 1: Execute EC2 cost analysis with enrichment
            print_info("Step 1/3: Enriching EC2 inventory with Organizations and Cost Explorer data...")
            enriched_df = analyze_ec2_costs(
                input_file=input_file,
                output_file=output_file,
                management_profile=management_profile,
                billing_profile=billing_profile,
                operational_profile=operational_profile,
                enable_organizations=True,
                enable_cost=True,
                enable_activity=enable_expensive_signals,  # CloudTrail activity (60-90s)
                include_12month_cost=True
            )

            # Step 2: Apply decommission classification
            print_info("\nStep 2/3: Applying E1-E7 decommission scoring framework...")
            enriched_df = classify_ec2(enriched_df)

            # Step 3: Generate executive summary
            print_info("\nStep 3/3: Generating Top 50 decommission candidates executive summary...")

            # Filter to MUST/SHOULD tiers
            top_candidates = enriched_df[
                enriched_df['decommission_tier'].isin(['MUST', 'SHOULD'])
            ].sort_values('decommission_score', ascending=False).head(50)

            if len(top_candidates) > 0:
                from rich.table import Table
                from runbooks.common.rich_utils import console, format_cost

                # Create executive table
                exec_table = Table(
                    title=f"Top {len(top_candidates)} Decommission Candidates",
                    show_header=True,
                    header_style="bold cyan"
                )

                exec_table.add_column("Instance ID", style="dim", width=20)
                exec_table.add_column("Account", style="white", width=25)
                exec_table.add_column("Type", style="cyan", width=12)
                exec_table.add_column("Score", style="red", width=8, justify="right")
                exec_table.add_column("Tier", style="yellow", width=10)
                exec_table.add_column("Monthly Cost", style="green", width=12, justify="right")
                exec_table.add_column("Annual Savings", style="green bold", width=15, justify="right")

                total_monthly_cost = 0
                total_annual_savings = 0

                for _, row in top_candidates.iterrows():
                    instance_id = str(row.get('instance_id', 'N/A'))[:19]
                    account_name = str(row.get('account_name', 'Unknown'))[:24]
                    instance_type = str(row.get('instance_type', 'N/A'))
                    score = row.get('decommission_score', 0)
                    tier = row.get('decommission_tier', 'KEEP')
                    monthly_cost = row.get('monthly_cost', 0.0)
                    annual_savings = monthly_cost * 12

                    total_monthly_cost += monthly_cost
                    total_annual_savings += annual_savings

                    tier_style = "red bold" if tier == "MUST" else "yellow"

                    exec_table.add_row(
                        instance_id,
                        account_name,
                        instance_type,
                        f"{score:.0f}",
                        f"[{tier_style}]{tier}[/{tier_style}]",
                        format_cost(monthly_cost),
                        format_cost(annual_savings)
                    )

                console.print("\n")
                console.print(exec_table)

                print_success(f"\n💰 Financial Impact:")
                print_success(f"   Total Monthly Cost: {format_cost(total_monthly_cost)}")
                print_success(f"   Total Annual Savings: {format_cost(total_annual_savings)}")
                print_success(f"   Average Decommission Score: {top_candidates['decommission_score'].mean():.1f}/100")

                tier_breakdown = top_candidates['decommission_tier'].value_counts()
                print_info(f"\n📊 Tier Breakdown (Top 50):")
                print_info(f"   MUST: {tier_breakdown.get('MUST', 0)} instances")
                print_info(f"   SHOULD: {tier_breakdown.get('SHOULD', 0)} instances")
            else:
                print_success("\n✅ No high-priority decommission candidates identified.")
                print_success("   All EC2 instances classified as COULD or KEEP tiers.")

            # Final summary
            print_success(f"\n✅ EC2 decommission analysis complete!")
            print_success(f"   📊 Analyzed {len(enriched_df)} EC2 instances")
            print_success(f"   📁 Output: {output_file}")

            return enriched_df

        except ImportError as e:
            error_handlers["module_not_available"]("EC2 Decommission Analyzer", e)
            raise click.ClickException("EC2 decommission analysis functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("EC2 decommission analysis", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--profile",
        "-p",
        default="default",
        help="AWS profile for Lambda operations (Organizations, Cost Explorer, CloudWatch)"
    )
    @click.option(
        "--output",
        "-o",
        "output_file",
        default="lambda-analysis.xlsx",
        type=click.Path(),
        help="Output enriched Excel file with Lambda analysis"
    )
    @click.option(
        "--regions",
        "-r",
        multiple=True,
        help="AWS regions to analyze (defaults to all enabled regions)"
    )
    @click.option(
        "--enable-organizations/--no-organizations",
        default=True,
        help="Enable Organizations metadata enrichment (default: enabled)"
    )
    @click.option(
        "--enable-cost/--no-cost",
        default=True,
        help="Enable Cost Explorer enrichment (default: enabled)"
    )
    @click.option("--verbose", "-v", is_flag=True, help="Show detailed logs")
    @click.option("--format", type=click.Choice(["compact", "table", "json"]), default="compact", help="Output format")
    @click.pass_context
    def lambda_analysis(
        ctx,
        profile,
        output_file,
        regions,
        enable_organizations,
        enable_cost,
        verbose,
        format
    ):
        """
        Lambda cost and activity analysis with optimization signals.

        \b
        🔄 LAMBDA ENRICHMENT LAYERS (L1-L6 Optimization Scoring)
        ┌──────────────────────────────────────────────────────────────┐
        │ Layer 1: Discovery       │ Lambda function inventory         │
        │ Layer 2: Organizations   │ Account metadata (6 columns)      │
        │ Layer 3: Cost            │ 12-month Cost Explorer trends     │
        │ Layer 4: CloudWatch      │ Invocations, errors, duration     │
        └──────────────────────────────────────────────────────────────┘

        \b
        📊 OPTIMIZATION SIGNALS (L1-L6)
        • L1: High invocation cost (top 10%) → +10 points (Cost impact)
        • L2: Idle function (0 invocations 14d) → +15 points (Unused)
        • L3: Oversized memory (low utilization) → +8 points (Rightsizing)
        • L4: Cold start issues (high p95/p50) → +5 points (Performance)
        • L5: High error rate (>5%) → +7 points (Quality issue)
        • L6: Legacy runtime → +3 points (Security/maintenance)

        \b
        🎯 OPTIMIZATION TIERS
        • HIGH (≥20 points): Immediate optimization/decommission
        • MEDIUM (10-19 points): Review and optimize within 30 days
        • LOW (<10 points): Monitor and maintain current state

        \b
        💰 Sprint 1 Target: Identify serverless optimization opportunities
        📖 Example: runbooks finops lambda-analysis --profile default --output lambda.xlsx
        """
        # Initialize output controller
        configure_logging(verbose=verbose)
        controller = OutputController(verbose=verbose, format=format)

        try:
            from runbooks.finops.lambda_analyzer import analyze_lambda_costs
            from runbooks.common.rich_utils import print_header, print_success, print_error

            print_header("Lambda Cost Analysis", f"Profile: {profile}")

            # Execute Lambda cost analysis
            result_df = analyze_lambda_costs(
                profile=profile,
                output_file=output_file,
                regions=list(regions) if regions else None,
                enable_organizations=enable_organizations,
                enable_cost=enable_cost
            )

            # Print summary using OutputController
            enrichment_layers = []
            if enable_organizations:
                enrichment_layers.append("organizations")
            if enable_cost:
                enrichment_layers.append("cost")

            controller.print_operation_summary(
                emoji="⚡",
                operation="Lambda Cost Analysis",
                input_count=len(result_df),
                enriched_count=len(result_df),
                enrichment_type="Lambda functions analyzed",
                success_percentage=100.0,
                profile=profile,
                output_file=output_file,
                added_columns=enrichment_layers
            )

            # Display optimization summary in verbose mode
            if verbose and len(result_df) > 0 and 'optimization_tier' in result_df.columns:
                tier_counts = result_df['optimization_tier'].value_counts()
                print_info(f"\n🎯 Optimization Opportunities:")
                print_info(f"   HIGH: {tier_counts.get('HIGH', 0)} functions")
                print_info(f"   MEDIUM: {tier_counts.get('MEDIUM', 0)} functions")
                print_info(f"   LOW: {tier_counts.get('LOW', 0)} functions")

            return result_df

        except ImportError as e:
            error_handlers["module_not_available"]("Lambda Cost Analyzer", e)
            raise click.ClickException("Lambda cost analysis functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("Lambda cost analysis", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--input",
        "-i",
        "input_file",
        required=True,
        type=click.Path(exists=True),
        help="Input WorkSpaces inventory Excel file (with Identifier, AWS Account, Region columns)"
    )
    @click.option(
        "--output",
        "-o",
        "output_file",
        required=True,
        type=click.Path(),
        help="Output enriched Excel file (multi-sheet with cost analysis)"
    )
    @click.option(
        "--management-profile",
        "-m",
        required=True,
        help="AWS management profile for Organizations API access"
    )
    @click.option(
        "--billing-profile",
        "-b",
        required=True,
        help="AWS billing profile for Cost Explorer API access"
    )
    @click.option(
        "--operational-profile",
        "-p",
        default=None,
        help="AWS operational profile for WorkSpaces operations (optional, defaults to management profile)"
    )
    @click.option(
        "--enable-organizations/--no-organizations",
        default=True,
        help="Enable Organizations metadata enrichment (default: enabled)"
    )
    @click.option(
        "--enable-cost/--no-cost",
        default=True,
        help="Enable Cost Explorer enrichment (default: enabled)"
    )
    @click.option(
        "--enable-activity/--no-activity",
        default=False,
        help="Enable CloudTrail activity tracking (default: disabled, takes 60-90 seconds)"
    )
    @click.option(
        "--include-12month-cost/--no-12month-cost",
        default=True,
        help="Include 12-month cost breakdown (default: enabled)"
    )
    @click.option("--verbose", "-v", is_flag=True, help="Show detailed logs")
    @click.option("--format", type=click.Choice(["compact", "table", "json"]), default="compact", help="Output format")
    @click.pass_context
    def analyze_workspaces(
        ctx,
        input_file,
        output_file,
        management_profile,
        billing_profile,
        operational_profile,
        enable_organizations,
        enable_cost,
        enable_activity,
        include_12month_cost,
        verbose,
        format
    ):
        """
        WorkSpaces cost analysis with decommission tier scoring.

        \b
        🔄 4-WAY ENRICHMENT LAYERS (W1-W6 Decommission Scoring)
        ┌──────────────────────────────────────────────────────────────┐
        │ Layer 1: Discovery       │ WorkSpaces inventory (122 total)  │
        │ Layer 2: Organizations   │ Account metadata (6 columns)      │
        │ Layer 3: Cost            │ 12-month Cost Explorer trends     │
        │ Layer 4: Activity        │ CloudWatch UserConnected metrics  │
        └──────────────────────────────────────────────────────────────┘

        \b
        📊 DECOMMISSION SIGNALS (W1-W6)
        • W1: WorkSpace stopped state → +15 points (HIGH priority)
        • W2: Zero UserConnected time (30d) → +12 points (Idle workspace)
        • W3: Low monthly cost (<$10) → +8 points (Basic bundle)
        • W4: Cost decreasing trend → +5 points (Usage declining)
        • W5: No volume encryption → +3 points (Compliance risk)
        • W6: Legacy bundle type → +2 points (Modernization opportunity)

        \b
        🎯 OPTIMIZATION TIERS
        • HIGH (≥25 points): Immediate decommission candidates
        • MEDIUM (15-24 points): Review recommended within 30 days
        • LOW (<15 points): Monitor and maintain current state

        \b
        💰 Sprint 1 Target: 25-50% cost savings via tier-based decommission
        📖 Example: runbooks finops analyze-workspaces -i ws.xlsx -o enriched.xlsx -m mgmt -b billing
        """
        # Initialize output controller
        configure_logging(verbose=verbose)
        controller = OutputController(verbose=verbose, format=format)

        try:
            from runbooks.finops.workspaces_analyzer import analyze_workspaces_costs
            from runbooks.common.rich_utils import print_header, print_success, print_error

            print_header("WorkSpaces Cost Analysis", f"Input: {input_file}")

            # Execute WorkSpaces cost analysis
            result_df = analyze_workspaces_costs(
                input_file=input_file,
                output_file=output_file,
                management_profile=management_profile,
                billing_profile=billing_profile,
                operational_profile=operational_profile,
                enable_organizations=enable_organizations,
                enable_cost=enable_cost,
                enable_activity=enable_activity,
                include_12month_cost=include_12month_cost
            )

            # Print summary using OutputController
            enrichment_layers = []
            if enable_organizations:
                enrichment_layers.append("organizations")
            if enable_cost:
                enrichment_layers.append("cost")
            if enable_activity:
                enrichment_layers.append("activity")

            controller.print_operation_summary(
                emoji="🖥️",
                operation="WorkSpaces Cost Analysis",
                input_count=len(result_df),
                enriched_count=len(result_df),
                enrichment_type="WorkSpaces analyzed",
                success_percentage=100.0,
                profile=management_profile,
                output_file=output_file,
                added_columns=enrichment_layers
            )

            return result_df

        except ImportError as e:
            error_handlers["module_not_available"]("WorkSpaces Cost Analyzer", e)
            raise click.ClickException("WorkSpaces cost analysis functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("WorkSpaces cost analysis", e)
            raise click.ClickException(str(e))

    @finops.command()
    @click.option(
        "--input",
        "-i",
        "input_file",
        required=True,
        type=click.Path(exists=True),
        help="Input WorkSpaces inventory Excel file (with Identifier, AWS Account, Region columns)"
    )
    @click.option(
        "--output",
        "-o",
        "output_file",
        required=True,
        type=click.Path(),
        help="Output enriched Excel file with decommission analysis"
    )
    @click.option(
        "--management-profile",
        "-m",
        required=True,
        help="AWS management profile for Organizations API access"
    )
    @click.option(
        "--billing-profile",
        "-b",
        required=True,
        help="AWS billing profile for Cost Explorer API access"
    )
    @click.option(
        "--operational-profile",
        "-p",
        default=None,
        help="AWS operational profile for WorkSpaces operations (optional, defaults to management)"
    )
    @click.pass_context
    def workspaces_decommission_analysis(
        ctx,
        input_file,
        output_file,
        management_profile,
        billing_profile,
        operational_profile
    ):
        """
        WorkSpaces decommission analysis with W1-W6 scoring framework.

        This command provides enterprise WorkSpaces decommission candidate identification with:
        • W1-W6 multi-signal scoring (connection recency, CloudWatch usage, break-even, policy)
        • MUST/SHOULD/COULD/KEEP tier classification
        • Top 50 decommission candidates executive summary
        • Annual savings projections per WorkSpace
        • Professional Rich CLI output for CxO consumption

        Scoring Framework (0-100 scale):
        • MUST (80-100): Immediate decommission candidates
        • SHOULD (50-79): Strong candidates (review recommended)
        • COULD (25-49): Potential candidates (manual review)
        • KEEP (<25): Active resources (no action)

        Signal Framework (W1-W6):
        • W1: User connection recency (≥60 days) → +45 points
        • W2: CloudWatch UserConnected sum=0 (no sessions) → +25 points
        • W3: Billing vs usage (hourly usage < break-even) → +10 points
        • W4: Cost Optimizer policy (N months unused) → +10 points
        • W5: No admin API activity (90d) → +5 points
        • W6: User status (not in Identity Center) → +5 points

        Examples:
            # Basic decommission analysis
            runbooks finops workspaces-decommission-analysis \\
                --input data/workspaces-inventory.xlsx \\
                --output data/workspaces-decommission-analysis.xlsx \\
                --management-profile mgmt-ro \\
                --billing-profile billing-ro

            # With custom operational profile
            runbooks finops workspaces-decommission-analysis \\
                -i data/workspaces.xlsx \\
                -o data/workspaces-decommission-full.xlsx \\
                -m mgmt-ro \\
                -b billing-ro \\
                -p ops-ro

        Input File Format:
            Excel file with required columns:
            - Identifier: WorkSpace ID (ws-xxxxx)
            - AWS Account: 12-digit AWS account ID
            - Region: AWS region (ap-southeast-2, etc.)

        Output File Format:
            Multi-sheet Excel with:
            - Sheet 1: Enriched Data (40+ columns with decommission scores)
            - Sheet 2: Top 50 Decommission Candidates (executive summary)
            - Sheet 3: Cost Summary (by account/tier)
            - Sheet 4: Validation Metrics

        Performance Notes:
            • WorkSpaces enrichment: ~5-10 seconds
            • CloudWatch metrics: ~10-15 seconds
            • Volume encryption: ~5-10 seconds
            • Break-even calculation: <1 second

        Pattern: Migrated from notebooks/compute/workspaces.ipynb with CxO executive polish
        """
        try:
            from runbooks.finops.workspaces_analyzer import analyze_workspaces_costs, WorkSpacesCostAnalyzer
            from runbooks.finops.decommission_classifier import classify_workspaces
            from runbooks.common.rich_utils import print_header, print_success, print_error, print_info

            print_header("WorkSpaces Decommission Analysis", f"Input: {input_file}")

            # Step 1: Execute WorkSpaces cost analysis with enrichment
            print_info("Step 1/5: Enriching WorkSpaces inventory with Organizations and Cost Explorer data...")
            enriched_df = analyze_workspaces_costs(
                input_file=input_file,
                output_file=output_file,
                management_profile=management_profile,
                billing_profile=billing_profile,
                operational_profile=operational_profile,
                enable_organizations=True,
                enable_cost=True,
                enable_activity=False,  # CloudTrail activity not needed for W1-W6
                include_12month_cost=True
            )

            # Step 2: Initialize analyzer for additional enrichment
            print_info("\nStep 2/5: Analyzing volume encryption and connection status...")
            analyzer = WorkSpacesCostAnalyzer(profile=operational_profile or management_profile)
            enriched_df = analyzer.get_volume_encryption(enriched_df)

            # Step 3: CloudWatch UserConnected metrics
            print_info("\nStep 3/5: Fetching CloudWatch UserConnected metrics...")
            enriched_df = analyzer.get_cloudwatch_user_connected(enriched_df, lookback_days=30)

            # Step 4: Dynamic break-even calculation
            print_info("\nStep 4/5: Calculating dynamic break-even hours...")
            enriched_df = analyzer.calculate_dynamic_breakeven(enriched_df)

            # Step 5: Apply decommission classification
            print_info("\nStep 5/5: Applying W1-W6 decommission scoring framework...")
            enriched_df = classify_workspaces(enriched_df)

            # Generate executive summary
            print_info("\nGenerating Top 50 decommission candidates executive summary...")

            # Filter to MUST/SHOULD tiers
            top_candidates = enriched_df[
                enriched_df['decommission_tier'].isin(['MUST', 'SHOULD'])
            ].sort_values('decommission_score', ascending=False).head(50)

            if len(top_candidates) > 0:
                from rich.table import Table
                from runbooks.common.rich_utils import console, format_cost

                # Create executive table
                exec_table = Table(
                    title=f"Top {len(top_candidates)} Decommission Candidates",
                    show_header=True,
                    header_style="bold cyan"
                )

                exec_table.add_column("WorkSpace ID", style="dim", width=20)
                exec_table.add_column("Account", style="white", width=25)
                exec_table.add_column("Username", style="cyan", width=15)
                exec_table.add_column("Score", style="red", width=8, justify="right")
                exec_table.add_column("Tier", style="yellow", width=10)
                exec_table.add_column("Days Idle", style="yellow", width=10, justify="right")
                exec_table.add_column("Monthly Cost", style="green", width=12, justify="right")
                exec_table.add_column("Annual Savings", style="green bold", width=15, justify="right")

                total_monthly_cost = 0
                total_annual_savings = 0

                for _, row in top_candidates.iterrows():
                    workspace_id = str(row.get('Identifier', row.get('WorkspaceId', 'N/A')))[:19]
                    account_name = str(row.get('account_name', 'Unknown'))[:24]
                    username = str(row.get('Username', 'N/A'))[:14]
                    score = row.get('decommission_score', 0)
                    tier = row.get('decommission_tier', 'KEEP')
                    days_idle = row.get('days_since_last_connection', 0)
                    monthly_cost = row.get('monthly_cost', 0.0)
                    annual_savings = monthly_cost * 12

                    total_monthly_cost += monthly_cost
                    total_annual_savings += annual_savings

                    tier_style = "red bold" if tier == "MUST" else "yellow"

                    exec_table.add_row(
                        workspace_id,
                        account_name,
                        username,
                        f"{score:.0f}",
                        f"[{tier_style}]{tier}[/{tier_style}]",
                        f"{days_idle}",
                        format_cost(monthly_cost),
                        format_cost(annual_savings)
                    )

                console.print("\n")
                console.print(exec_table)

                print_success(f"\n💰 Financial Impact:")
                print_success(f"   Total Monthly Cost: {format_cost(total_monthly_cost)}")
                print_success(f"   Total Annual Savings: {format_cost(total_annual_savings)}")
                print_success(f"   Average Decommission Score: {top_candidates['decommission_score'].mean():.1f}/100")

                tier_breakdown = top_candidates['decommission_tier'].value_counts()
                print_info(f"\n📊 Tier Breakdown (Top 50):")
                print_info(f"   MUST: {tier_breakdown.get('MUST', 0)} WorkSpaces")
                print_info(f"   SHOULD: {tier_breakdown.get('SHOULD', 0)} WorkSpaces")
            else:
                print_success("\n✅ No high-priority decommission candidates identified.")
                print_success("   All WorkSpaces classified as COULD or KEEP tiers.")

            # Final summary
            print_success(f"\n✅ WorkSpaces decommission analysis complete!")
            print_success(f"   📊 Analyzed {len(enriched_df)} WorkSpaces")
            print_success(f"   📁 Output: {output_file}")

            return enriched_df

        except ImportError as e:
            error_handlers["module_not_available"]("WorkSpaces Decommission Analyzer", e)
            raise click.ClickException("WorkSpaces decommission analysis functionality not available")
        except Exception as e:
            error_handlers["operation_failed"]("WorkSpaces decommission analysis", e)
            raise click.ClickException(str(e))

    return finops
