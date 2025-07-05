"""Main CLI application entry point"""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, Dict, List, Any
import sys

from ..core.engine import RuleEngine
from ..database.manager import DatabaseManager
from ..rules.manager import RuleManager

console = Console()
app = typer.Typer(
    name="eda-rule-engine",
    help="Data Accuracy Test Rule Engine - Validate business logic rules across databases",
    rich_markup_mode="rich"
)

# Sub-commands
config_app = typer.Typer(name="config", help="Database configuration management")
rule_app = typer.Typer(name="rule", help="Rule management and execution")
report_app = typer.Typer(name="report", help="Generate validation reports")

app.add_typer(config_app, name="config")
app.add_typer(rule_app, name="rule") 
app.add_typer(report_app, name="report")

@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of the project"),
    database_type: str = typer.Option("postgresql", help="Database type (postgresql, mysql, sqlite)")
):
    """Initialize a new EDA Rule Engine project"""
    console.print(f"🚀 Initializing new project: [bold cyan]{project_name}[/bold cyan]")
    
    # Create project configuration
    from ..utils.config import ConfigManager
    config_manager = ConfigManager()
    config_manager.init_project(project_name, database_type)
    
    console.print("✅ Project initialized successfully!")
    console.print("📝 Configuration saved to: [dim].eda-config.yaml[/dim]")
    console.print("\n📖 Next steps:")
    console.print("1. Configure database: [cyan]eda-rule-engine config add-db[/cyan]")
    console.print("2. Create your first rule: [cyan]eda-rule-engine rule create[/cyan]")

@config_app.command("add-db")
def add_database(
    name: str = typer.Argument(..., help="Database connection name"),
    db_type: str = typer.Option(..., "--type", help="Database type (postgresql, mysql, sqlite)"),
    host: str = typer.Option("localhost", help="Database host"),
    port: Optional[int] = typer.Option(None, help="Database port"),
    database: str = typer.Option(..., help="Database name"),
    username: Optional[str] = typer.Option(None, help="Username"),
    password: Optional[str] = typer.Option(None, help="Password (will be prompted securely)")
):
    """Add a new database connection"""
    console.print(f"🔗 Adding database connection: [bold cyan]{name}[/bold cyan]")
    
    # Prompt for password securely if not provided
    if password is None and db_type != "sqlite":
        password = typer.prompt("Password", hide_input=True)
    
    # Set default ports
    if port is None:
        port = {"postgresql": 5432, "mysql": 3306}.get(db_type, 5432)
    
    db_manager = DatabaseManager()
    try:
        db_manager.add_connection(name, db_type, host, port, database, username, password)
        console.print("✅ Database connection added successfully!")
        
        # Test connection
        if db_manager.test_connection(name):
            console.print("🔍 Connection test: [green]PASSED[/green]")
        else:
            console.print("⚠️  Connection test: [red]FAILED[/red]")
            
    except Exception as e:
        console.print(f"❌ Error adding database: {e}")
        sys.exit(1)

@config_app.command("list-db")
def list_databases():
    """List all configured database connections"""
    db_manager = DatabaseManager()
    connections = db_manager.list_connections()
    
    if not connections:
        console.print("📭 No database connections configured")
        return
    
    table = Table(title="Database Connections")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Host", style="green")
    table.add_column("Database", style="yellow")
    table.add_column("Status", style="bold")
    
    for conn in connections:
        status = "🟢 Active" if db_manager.test_connection(str(conn['name'])) else "🔴 Inactive"
        table.add_row(
            str(conn['name']),
            str(conn['type']),
            str(conn['host']),
            str(conn['database']),
            status
        )
    
    console.print(table)

@rule_app.command("create")
def create_rule(
    name: str = typer.Argument(..., help="Rule name"),
    rule_type: str = typer.Option(..., "--type", help="Rule type (value_range, value_template, data_continuity, statistical_comparison, cross_table_comparison)"),
    table: str = typer.Option(..., help="Target table (schema.table)"),
    column: Optional[str] = typer.Option(None, help="Target column"),
    description: str = typer.Option("", help="Rule description")
):
    """Create a new validation rule"""
    console.print(f"📝 Creating rule: [bold cyan]{name}[/bold cyan]")
    
    rule_manager = RuleManager()
    
    try:
        # Interactive rule creation based on type
        rule_config = _interactive_rule_creation(rule_type, table, column)
        rule_id = rule_manager.create_rule(name, rule_type, rule_config, description)
        
        console.print(f"✅ Rule created successfully! ID: [green]{rule_id}[/green]")
        console.print(f"🔍 Test the rule: [cyan]eda-rule-engine rule run {rule_id}[/cyan]")
        
    except Exception as e:
        console.print(f"❌ Error creating rule: {e}")
        sys.exit(1)

@rule_app.command("list")
def list_rules(
    status: Optional[str] = typer.Option(None, help="Filter by status (active, inactive)")
):
    """List all validation rules"""
    rule_manager = RuleManager()
    rules = rule_manager.list_rules(status)
    
    if not rules:
        console.print("📭 No rules found")
        return
    
    table = Table(title="Validation Rules")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Type", style="magenta")
    table.add_column("Target", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Last Run", style="dim")
    
    for rule in rules:
        table.add_row(
            str(rule['id']),
            str(rule['name']),
            str(rule['type']),
            f"{rule['table']}.{rule.get('column', '*')}",
            str(rule['status']),
            str(rule.get('last_run', 'Never'))
        )
    
    console.print(table)

@rule_app.command("run")
def run_rule(
    rule_id: str = typer.Argument(..., help="Rule ID or name to execute"),
    database: Optional[str] = typer.Option(None, help="Database connection to use"),
    output_format: str = typer.Option("table", help="Output format (table, json, csv)")
):
    """Execute a validation rule"""
    console.print(f"⚡ Running rule: [bold cyan]{rule_id}[/bold cyan]")
    
    engine = RuleEngine()
    
    try:
        with console.status("[bold green]Executing rule..."):
            result = engine.execute_rule(rule_id, database)
        
        _display_rule_result(result, output_format)
        
    except Exception as e:
        console.print(f"❌ Error executing rule: {e}")
        sys.exit(1)

@rule_app.command("run-batch")
def run_batch_rules(
    table: Optional[str] = typer.Option(None, help="Run all rules for specific table"),
    tag: Optional[str] = typer.Option(None, help="Run rules with specific tag"),
    database: Optional[str] = typer.Option(None, help="Database connection to use")
):
    """Execute multiple validation rules"""
    console.print("⚡ Running batch validation...")
    
    engine = RuleEngine()
    
    try:
        with console.status("[bold green]Executing rules..."):
            results = engine.execute_batch_rules(table=table, tag=tag, database=database)
        
        _display_batch_results(results)
        
    except Exception as e:
        console.print(f"❌ Error executing batch rules: {e}")
        sys.exit(1)

@report_app.command("summary")
def generate_summary_report(
    database: Optional[str] = typer.Option(None, help="Database to report on"),
    days: int = typer.Option(7, help="Number of days to include in report")
):
    """Generate a summary validation report"""
    console.print(f"📊 Generating summary report for last {days} days...")
    
    from ..core.reporter import Reporter
    reporter = Reporter()
    
    try:
        report = reporter.generate_summary_report(database, days)
        _display_summary_report(report)
        
    except Exception as e:
        console.print(f"❌ Error generating report: {e}")
        sys.exit(1)

def _interactive_rule_creation(rule_type: str, table: str, column: Optional[str]) -> Dict[str, Any]:
    """Interactive rule configuration based on rule type"""
    config: Dict[str, Any] = {"table": table, "column": column}
    
    if rule_type == "value_range":
        config["min_value"] = typer.prompt("Minimum value", type=float)
        config["max_value"] = typer.prompt("Maximum value", type=float)
        
    elif rule_type == "value_template":
        config["pattern"] = typer.prompt("Regex pattern")
        
    elif rule_type == "statistical_comparison":
        config["operation"] = typer.prompt("Statistical operation (sum, avg, min, max, count)")
        config["compare_table"] = typer.prompt("Comparison table")
        config["compare_column"] = typer.prompt("Comparison column")
        config["threshold"] = typer.prompt("Threshold (default: 0.05)", default=0.05, type=float)
        
    elif rule_type == "cross_table_comparison":
        config["compare_table"] = typer.prompt("Comparison table")
        config["compare_column"] = typer.prompt("Comparison column")
        config["join_key"] = typer.prompt("Join key (default: id)", default="id")
        config["operation"] = typer.prompt("Aggregation operation (SUM, AVG, COUNT)", default="SUM")
        
    elif rule_type == "data_continuity":
        config["check_type"] = typer.prompt("Check type (sequence_gaps, null_values)", default="null_values")
        
    return config

def _display_rule_result(result: Dict[str, Any], output_format: str):
    """Display rule execution result"""
    if output_format == "json":
        console.print_json(data=result)
        return
    
    # Table format
    console.print("\n📊 [bold]Validation Result[/bold]")
    console.print(f"Rule: [cyan]{result['rule_name']}[/cyan]")
    console.print(f"Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    console.print(f"Records Processed: [yellow]{result['total_records']}[/yellow]")
    console.print(f"Pass Rate: [green]{result['pass_rate']:.2f}%[/green]")
    
    if result['failed_records'] > 0:
        console.print(f"Failed Records: [red]{result['failed_records']}[/red]")

def _display_batch_results(results: List[Dict[str, Any]]):
    """Display batch rule execution results"""
    table = Table(title="Batch Validation Results")
    table.add_column("Rule", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Records", style="yellow")
    table.add_column("Pass Rate", style="green")
    
    total_rules = len(results)
    passed_rules = sum(1 for r in results if r.get('passed', False))
    
    for result in results:
        status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
        table.add_row(
            str(result.get('rule_name', 'Unknown')),
            status,
            str(result.get('total_records', 0)),
            f"{result.get('pass_rate', 0):.1f}%"
        )
    
    console.print(table)
    console.print(f"\n📈 Overall: {passed_rules}/{total_rules} rules passed ({passed_rules/total_rules*100:.1f}%)")

def _display_summary_report(report: Dict[str, Any]):
    """Display summary report"""
    console.print("📊 [bold]Data Quality Summary Report[/bold]\n")
    
    # Overall metrics
    console.print(f"🎯 Overall Quality Score: [bold green]{report.get('overall_score', 0):.1f}%[/bold green]")
    console.print(f"📊 Total Rules Executed: {report.get('total_rules', 0)}")
    console.print(f"📈 Average Pass Rate: {report.get('avg_pass_rate', 0):.1f}%")
    
    # Top issues
    top_issues = report.get('top_issues', [])
    if top_issues:
        console.print("\n🔍 Top Issues:")
        for issue in top_issues[:5]:
            if isinstance(issue, dict):
                rule_name = issue.get('rule_name', 'Unknown')
                failure_rate = issue.get('failure_rate', 0)
                console.print(f"  • {rule_name}: {failure_rate:.1f}% failure rate")

if __name__ == "__main__":
    app()