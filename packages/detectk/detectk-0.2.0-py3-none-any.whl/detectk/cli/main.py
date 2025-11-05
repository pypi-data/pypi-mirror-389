"""DetectK CLI main entry point.

This module provides the main CLI interface using Click framework.
"""

import logging
import sys
from pathlib import Path
from typing import Any

import click

from detectk import __version__
from detectk.check import MetricCheck
from detectk.cli.init_project import (
    copy_examples,
    create_project_structure,
    init_git_repo,
)
from detectk.config.loader import ConfigLoader
from detectk.exceptions import ConfigurationError, DetectKError
from detectk.registry import AlerterRegistry, CollectorRegistry, DetectorRegistry

# Import packages to trigger auto-registration
try:
    import detectk_clickhouse  # noqa: F401
except ImportError:
    pass

try:
    import detectk_detectors  # noqa: F401
except ImportError:
    pass

try:
    import detectk_alerters_mattermost  # noqa: F401
except ImportError:
    pass

try:
    import detectk_alerters_slack  # noqa: F401
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="dtk")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (DEBUG level)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress all output except errors",
)
def cli(verbose: bool, quiet: bool) -> None:
    """DetectK - Flexible anomaly detection and alerting for metrics.

    Monitor database metrics, detect anomalies using various algorithms,
    and send alerts through multiple channels.

    \b
    Examples:
        dtk run configs/sessions.yaml
        dtk validate configs/revenue.yaml
        dtk list-detectors
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


@cli.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--execution-time",
    "-t",
    type=str,
    help="Override execution time (ISO format: YYYY-MM-DD HH:MM:SS)",
)
def run(config_path: Path, execution_time: str | None) -> None:
    """Run metric check from configuration file.

    CONFIG_PATH: Path to YAML configuration file

    \b
    Examples:
        # Run with current time
        dtk run configs/sessions.yaml

        # Run with specific execution time
        dtk run configs/sessions.yaml -t "2024-11-01 14:30:00"
    """
    try:
        click.echo(f"📊 Running metric check: {config_path}")

        # Parse execution time if provided
        exec_time = None
        if execution_time:
            from datetime import datetime

            exec_time = datetime.fromisoformat(execution_time)
            click.echo(f"⏰ Execution time: {exec_time}")

        # Run check
        checker = MetricCheck()
        result = checker.execute(str(config_path), execution_time=exec_time)

        # Display results
        click.echo()
        click.echo("=" * 70)
        click.echo("RESULTS")
        click.echo("=" * 70)
        click.echo(f"Metric: {result.metric_name}")
        click.echo(f"Timestamp: {result.timestamp}")
        click.echo(f"Value: {result.value:,.2f}")
        click.echo()

        if result.detections:
            click.echo("Detections:")
            for detection in result.detections:
                status = "🚨 ANOMALY" if detection.is_anomaly else "✅ NORMAL"
                click.echo(f"  [{detection.metadata.get('detector_id', 'unknown')}] {status}")
                if detection.is_anomaly:
                    if detection.score is not None:
                        click.echo(f"    Score: {detection.score:.2f} sigma")
                    if detection.direction:
                        click.echo(f"    Direction: {detection.direction}")
                    if detection.percent_deviation is not None:
                        click.echo(f"    Deviation: {detection.percent_deviation:+.1f}%")
        else:
            click.echo("No detections configured")

        click.echo()
        if result.alert_sent:
            click.echo(f"✉️  Alert sent: {result.alert_reason}")
        elif result.detections and any(d.is_anomaly for d in result.detections):
            click.echo("⏭️  Alert skipped (cooldown or other condition)")
        else:
            click.echo("📧 No alert sent (no anomaly detected)")

        if result.errors:
            click.echo()
            click.echo("⚠️  Errors:")
            for error in result.errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        click.echo()
        click.echo("✅ Check completed successfully")

    except ConfigurationError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)
    except DetectKError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error")
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
def validate(config_path: Path) -> None:
    """Validate configuration file without running check.

    CONFIG_PATH: Path to YAML configuration file

    \b
    Example:
        dtk validate configs/sessions.yaml
    """
    try:
        click.echo(f"🔍 Validating configuration: {config_path}")

        # Load and validate config
        loader = ConfigLoader()
        config = loader.load_file(str(config_path))

        click.echo()
        click.echo("=" * 70)
        click.echo("CONFIGURATION SUMMARY")
        click.echo("=" * 70)
        click.echo(f"Metric: {config.name}")
        if config.description:
            click.echo(f"Description: {config.description}")

        click.echo()
        click.echo(f"Collector: {config.collector.type}")
        click.echo(f"Storage: {config.storage.type if config.storage and config.storage.enabled else 'disabled'}")

        click.echo()
        detectors = config.get_detectors()
        click.echo(f"Detectors: {len(detectors)}")
        for detector in detectors:
            detector_id = detector.id or "auto-generated"
            click.echo(f"  - {detector.type} (ID: {detector_id})")

        if config.alerter:
            click.echo()
            click.echo(f"Alerter: {config.alerter.type}")

        click.echo()
        click.echo("✅ Configuration is valid!")

    except ConfigurationError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during validation")
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command("list-collectors")
def list_collectors() -> None:
    """List available data collectors.

    \b
    Example:
        dtk list-collectors
    """
    click.echo("📡 Available Collectors:")
    click.echo()

    collectors = CollectorRegistry.list_all()
    if not collectors:
        click.echo("  No collectors registered")
        return

    for name in sorted(collectors):
        collector_class = CollectorRegistry.get(name)
        docstring = collector_class.__doc__ or "No description"
        # First line of docstring
        description = docstring.strip().split("\n")[0]
        click.echo(f"  • {name:15s} - {description}")


@cli.command("list-detectors")
def list_detectors() -> None:
    """List available anomaly detectors.

    \b
    Example:
        dtk list-detectors
    """
    click.echo("🔍 Available Detectors:")
    click.echo()

    detectors = DetectorRegistry.list_all()
    if not detectors:
        click.echo("  No detectors registered")
        return

    for name in sorted(detectors):
        detector_class = DetectorRegistry.get(name)
        docstring = detector_class.__doc__ or "No description"
        # First line of docstring
        description = docstring.strip().split("\n")[0]
        click.echo(f"  • {name:15s} - {description}")


@cli.command("list-alerters")
def list_alerters() -> None:
    """List available alerters.

    \b
    Example:
        dtk list-alerters
    """
    click.echo("📢 Available Alerters:")
    click.echo()

    alerters = AlerterRegistry.list_all()
    if not alerters:
        click.echo("  No alerters registered")
        return

    for name in sorted(alerters):
        alerter_class = AlerterRegistry.get(name)
        docstring = alerter_class.__doc__ or "No description"
        # First line of docstring
        description = docstring.strip().split("\n")[0]
        click.echo(f"  • {name:15s} - {description}")


@cli.command("list-metrics")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Directory to search for metric configs (default: current directory)",
)
@click.option(
    "--details",
    is_flag=True,
    help="Show detailed information about each metric",
)
@click.option(
    "--validate",
    is_flag=True,
    help="Validate each metric configuration",
)
@click.option(
    "--collector",
    "-c",
    help="Filter by collector type (e.g., clickhouse, sql, http)",
)
@click.option(
    "--tags",
    "-t",
    multiple=True,
    help="Filter by tags (can be used multiple times)",
)
@click.option(
    "--match-all-tags",
    is_flag=True,
    help="Require ALL specified tags to match (default: match ANY tag)",
)
def list_metrics(
    path: Path,
    details: bool,
    validate: bool,
    collector: str | None,
    tags: tuple[str, ...],
    match_all_tags: bool,
) -> None:
    """List all metric configurations in the project.

    Scans directories for .yaml files and displays configured metrics.

    \b
    Examples:
        # List all metrics in current directory
        dtk list-metrics

        # List metrics in specific directory
        dtk list-metrics --path configs/

        # Show detailed information
        dtk list-metrics --details

        # Validate all metrics
        dtk list-metrics --validate

        # Filter by collector type
        dtk list-metrics --collector clickhouse
    """
    click.echo("📊 DetectK Metrics:")
    click.echo()

    # Strict structure: all metrics must be in "metrics/" directory
    # (like dbt's "models/" directory)
    metrics_dir = path / "metrics"

    if not metrics_dir.exists():
        click.echo("  ❌ No 'metrics/' directory found")
        click.echo(f"  Expected location: {metrics_dir}")
        click.echo()
        click.echo("  💡 Initialize a DetectK project with:")
        click.echo("     dtk init-project")
        return

    # Find all .yaml files recursively in metrics/ directory
    yaml_files = []
    yaml_files.extend(metrics_dir.glob("**/*.yaml"))
    yaml_files.extend(metrics_dir.glob("**/*.yml"))

    if not yaml_files:
        click.echo("  No metric configuration files found in metrics/")
        click.echo(f"  Directory: {metrics_dir}")
        click.echo()
        click.echo("  💡 Create a metric config:")
        click.echo("     dtk init metrics/my_metric.yaml")
        return

    # Load and display metrics
    config_loader = ConfigLoader()
    metrics_found = 0
    metrics_valid = 0
    metrics_filtered = 0

    for yaml_file in sorted(yaml_files):
        # Skip template files
        if yaml_file.name.endswith(".template"):
            continue

        try:
            # Try to load config (lenient mode - allow missing env vars)
            config = config_loader.load_file(str(yaml_file), lenient=True)

            # Filter by collector if specified
            if collector and config.collector.type != collector:
                metrics_filtered += 1
                continue

            # Filter by tags if specified
            if tags:
                metric_tags_set = set(config.tags) if config.tags else set()
                required_tags_set = set(tags)

                if match_all_tags:
                    # ALL tags must match
                    if not required_tags_set.issubset(metric_tags_set):
                        metrics_filtered += 1
                        continue
                else:
                    # ANY tag must match
                    if not (required_tags_set & metric_tags_set):
                        metrics_filtered += 1
                        continue

            metrics_found += 1

            # Display metric
            # Show path relative to metrics/ directory (not project root)
            rel_path = yaml_file.relative_to(metrics_dir)

            if details:
                click.echo("─" * 70)
                click.echo(f"📌 {config.name}")
                click.echo(f"   File: metrics/{rel_path}")
                if config.description:
                    click.echo(f"   Description: {config.description}")
                click.echo(f"   Collector: {config.collector.type}")

                # Detectors
                detectors = config.get_detectors()
                detector_info = ", ".join(
                    f"{d.type}(id={d.id[:8] if d.id else 'auto'})" for d in detectors
                )
                click.echo(f"   Detectors: {detector_info}")

                # Alerter
                alerter_info = config.alerter.type if config.alerter else "none"
                click.echo(f"   Alerter: {alerter_info}")

                # Storage
                storage_info = (
                    f"{config.storage.type} (enabled)"
                    if config.storage and config.storage.enabled
                    else "disabled"
                )
                click.echo(f"   Storage: {storage_info}")

                # Tags
                if config.tags:
                    tags_str = ", ".join(config.tags)
                    click.echo(f"   Tags: {tags_str}")

                if validate:
                    click.echo("   Status: ✅ Valid")
                    metrics_valid += 1

                click.echo()
            else:
                # Simple format
                collector_info = f"[{config.collector.type}]"
                tags_info = f"[{', '.join(config.tags)}]" if config.tags else ""
                file_path = f"metrics/{rel_path}"
                status = "✅" if validate else ""

                if validate:
                    metrics_valid += 1

                # Format output with tags
                if tags_info:
                    click.echo(f"  {status} {config.name:30s} {collector_info:15s} {tags_info:30s} {file_path}")
                else:
                    click.echo(f"  {status} {config.name:30s} {collector_info:15s} {file_path}")

        except ConfigurationError as e:
            # Configuration error - show in output
            rel_path = yaml_file.relative_to(metrics_dir)

            if details:
                click.echo("─" * 70)
                click.echo(f"📌 {yaml_file.name}")
                click.echo(f"   File: metrics/{rel_path}")
                click.echo(f"   Status: ❌ Invalid - {e}")
                click.echo()
            else:
                file_path = f"metrics/{rel_path}"
                click.echo(f"  ❌ {yaml_file.stem:30s} {'[error]':15s} {file_path}")

            metrics_found += 1
            continue

        except Exception as e:
            # Unexpected error - skip this file
            logger.debug(f"Skipping {yaml_file}: {e}")
            continue

    # Summary
    click.echo()
    click.echo("─" * 70)
    click.echo(f"Total: {metrics_found} metrics found")

    if collector:
        click.echo(f"Filtered: {metrics_filtered} metrics excluded (collector != {collector})")

    if validate:
        click.echo(f"Valid: {metrics_valid}/{metrics_found}")


@cli.command()
@click.argument("output_path", type=click.Path(path_type=Path), default="metric_config.yaml")
@click.option(
    "--detector",
    "-d",
    type=click.Choice(["threshold", "mad", "zscore"]),
    default="threshold",
    help="Detector type to use in template",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing file",
)
def init(output_path: Path, detector: str, overwrite: bool) -> None:
    """Generate template configuration file.

    OUTPUT_PATH: Path where to create config file (default: metric_config.yaml)

    \b
    Examples:
        # Create template with threshold detector
        dtk init

        # Create template with MAD detector
        dtk init my_config.yaml -d mad

        # Overwrite existing file
        dtk init my_config.yaml --overwrite
    """
    # Check if file exists
    if output_path.exists() and not overwrite:
        click.echo(f"❌ File already exists: {output_path}", err=True)
        click.echo("   Use --overwrite to replace it", err=True)
        sys.exit(1)

    # Template configurations for different detectors
    templates = {
        "threshold": """# DetectK Configuration - Threshold Detector
# Simple threshold-based anomaly detection

name: "my_metric"
description: "Describe your metric here"

# Data Collection
collector:
  type: "clickhouse"
  params:
    host: "${CLICKHOUSE_HOST:-localhost}"
    port: 9000
    database: "your_database"
    query: |
      SELECT
        count(*) as value,
        now() as timestamp
      FROM your_table
      WHERE timestamp >= now() - INTERVAL 1 HOUR

# Anomaly Detection
detector:
  type: "threshold"
  params:
    operator: "greater_than"  # greater_than, less_than, between, outside, etc.
    threshold: 1000           # Adjust based on your metric

# Alert Delivery
alerter:
  type: "mattermost"
  params:
    webhook_url: "${MATTERMOST_WEBHOOK}"
    cooldown_minutes: 60  # Wait 1 hour between alerts

# Historical Data Storage (optional)
storage:
  enabled: false  # Set to true to enable historical data storage
  # type: "clickhouse"
  # params:
  #   host: "${CLICKHOUSE_HOST:-localhost}"
  #   database: "detectk"
  #   datapoints_retention_days: 90
""",
        "mad": """# DetectK Configuration - MAD Detector
# Statistical anomaly detection using Median Absolute Deviation
# Robust to outliers, good for "dirty" data

name: "my_metric"
description: "Describe your metric here"

# Data Collection
collector:
  type: "clickhouse"
  params:
    host: "${CLICKHOUSE_HOST:-localhost}"
    port: 9000
    database: "your_database"
    query: |
      SELECT
        count(*) as value,
        now() as timestamp
      FROM your_table
      WHERE timestamp >= now() - INTERVAL 10 MINUTE

# Anomaly Detection
detector:
  type: "mad"
  params:
    window_size: "30 days"   # Historical window for comparison
    n_sigma: 3.0             # Alert if value > median + 3*MAD_sigma
    use_weighted: true       # Weight recent data more (exponential decay)
    exp_decay_factor: 0.1    # Higher = more weight to recent data

# Alert Delivery
alerter:
  type: "mattermost"
  params:
    webhook_url: "${MATTERMOST_WEBHOOK}"
    cooldown_minutes: 60

# Historical Data Storage (required for MAD detector)
storage:
  enabled: true
  type: "clickhouse"
  params:
    host: "${CLICKHOUSE_HOST:-localhost}"
    database: "detectk"
    datapoints_retention_days: 90
    save_detections: false  # Save space - only store raw values
""",
        "zscore": """# DetectK Configuration - Z-Score Detector
# Statistical anomaly detection using mean and standard deviation
# Faster than MAD, less robust to outliers

name: "my_metric"
description: "Describe your metric here"

# Data Collection
collector:
  type: "clickhouse"
  params:
    host: "${CLICKHOUSE_HOST:-localhost}"
    port: 9000
    database: "your_database"
    query: |
      SELECT
        sum(amount) as value,
        now() as timestamp
      FROM transactions
      WHERE timestamp >= now() - INTERVAL 1 HOUR

# Anomaly Detection
detector:
  type: "zscore"
  params:
    window_size: "7 days"    # Historical window for comparison
    n_sigma: 3.0             # Alert if value > mean + 3*std
    use_weighted: true       # Weight recent data more
    exp_decay_factor: 0.1

# Alert Delivery
alerter:
  type: "mattermost"
  params:
    webhook_url: "${MATTERMOST_WEBHOOK}"
    cooldown_minutes: 120  # Wait 2 hours for revenue alerts

# Historical Data Storage (required for Z-score detector)
storage:
  enabled: true
  type: "clickhouse"
  params:
    host: "${CLICKHOUSE_HOST:-localhost}"
    database: "detectk"
    datapoints_retention_days: 90
    save_detections: false
""",
    }

    # Get template content
    template_content = templates[detector]

    # Write to file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template_content)

        click.echo(f"✅ Created configuration file: {output_path}")
        click.echo()
        click.echo(f"Detector type: {detector}")
        click.echo()
        click.echo("Next steps:")
        click.echo("1. Edit the configuration file:")
        click.echo(f"   - Update collector query for your data")
        click.echo(f"   - Adjust detector parameters")
        click.echo(f"   - Set CLICKHOUSE_HOST and MATTERMOST_WEBHOOK environment variables")
        click.echo()
        click.echo("2. Validate configuration:")
        click.echo(f"   dtk validate {output_path}")
        click.echo()
        click.echo("3. Run metric check:")
        click.echo(f"   dtk run {output_path}")

    except Exception as e:
        click.echo(f"❌ Error creating file: {e}", err=True)
        sys.exit(1)


@cli.command("init-project")
@click.argument("directory", type=click.Path(path_type=Path), default=".")
@click.option(
    "--database",
    "-d",
    type=click.Choice(["clickhouse", "postgres", "mysql", "sqlite"]),
    default="clickhouse",
    help="Primary database type",
)
@click.option(
    "--minimal",
    is_flag=True,
    help="Create minimal structure (no examples)",
)
@click.option(
    "--no-git",
    is_flag=True,
    help="Skip git repository initialization",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode (ask questions)",
)
def init_project(
    directory: Path,
    database: str,
    minimal: bool,
    no_git: bool,
    interactive: bool,
) -> None:
    """Initialize a new DetectK project with complete structure.

    Creates a ready-to-use project directory with:
    - Connection profile templates
    - Environment variable templates
    - .gitignore for credentials
    - README with setup instructions
    - Example metric configuration
    - Optional: Reference examples from library

    DIRECTORY: Project directory (default: current directory)

    \b
    Examples:
        # Initialize in current directory
        dtk init-project

        # Create new project directory
        dtk init-project my-metrics-monitoring

        # Interactive mode
        dtk init-project --interactive

        # Minimal (no examples)
        dtk init-project my-project --minimal

        # PostgreSQL instead of ClickHouse
        dtk init-project my-project -d postgres
    """
    # Interactive mode
    if interactive:
        click.echo()
        click.echo("╔════════════════════════════════════════════════════════╗")
        click.echo("║         DetectK Project Initialization                 ║")
        click.echo("╚════════════════════════════════════════════════════════╝")
        click.echo()

        # Ask project name if directory is current
        if directory == Path("."):
            project_name = click.prompt(
                "Project name",
                default="my-detectk-project",
                type=str,
            )
            directory = Path(project_name)

        # Ask database type
        database = click.prompt(
            "Primary database",
            type=click.Choice(["clickhouse", "postgres", "mysql", "sqlite"]),
            default=database,
        )

        # Ask about examples
        include_examples = click.confirm(
            "Include example configurations?",
            default=True,
        )
        minimal = not include_examples

        # Ask about git
        init_git = click.confirm("Initialize git repository?", default=True)
        no_git = not init_git

        click.echo()

    # Resolve directory
    project_dir = directory.resolve()

    # Check if directory exists and is not empty
    if project_dir.exists() and any(project_dir.iterdir()):
        if not click.confirm(
            f"Directory '{project_dir}' is not empty. Continue?",
            default=False,
        ):
            click.echo("Aborted.")
            sys.exit(0)

    try:
        # Create project structure
        click.echo(f"Creating project structure in: {project_dir}")
        click.echo()

        created_files = create_project_structure(
            project_dir,
            include_examples=not minimal,
            minimal=minimal,
        )

        # Report created files
        click.echo("✓ Created project structure:")
        click.echo(f"  • detectk_profiles.yaml.template")
        click.echo(f"  • .env.template")
        click.echo(f"  • .gitignore")
        click.echo(f"  • README.md")
        click.echo(f"  • metrics/example_metric.yaml")

        # Copy examples if requested
        if not minimal:
            # Try to find examples in package
            try:
                import detectk

                package_root = Path(detectk.__file__).parent.parent.parent.parent
                examples_source = package_root / "examples"

                if examples_source.exists():
                    copied = copy_examples(project_dir, examples_source)
                    if copied > 0:
                        click.echo(f"✓ Copied {copied} example configuration(s)")
                else:
                    click.echo("⚠ Example configurations not found (install from source)")
            except Exception as e:
                click.echo(f"⚠ Could not copy examples: {e}")

        # Initialize git repository
        if not no_git:
            if init_git_repo(project_dir):
                click.echo("✓ Initialized git repository")
            else:
                click.echo("⚠ Could not initialize git repository (git not found?)")

        # Display next steps
        click.echo()
        click.echo("=" * 70)
        click.echo("NEXT STEPS")
        click.echo("=" * 70)
        click.echo()

        # Navigation step if directory was created
        if project_dir != Path(".").resolve():
            click.echo(f"1. cd {project_dir.name}")
            click.echo()

        click.echo("2. Set up credentials:")
        click.echo("   cp detectk_profiles.yaml.template detectk_profiles.yaml")
        click.echo("   cp .env.template .env")
        click.echo()

        click.echo("3. Edit with your credentials:")
        click.echo("   vim detectk_profiles.yaml")
        click.echo("   vim .env")
        click.echo()

        click.echo("4. Load environment variables:")
        click.echo("   source .env")
        click.echo()

        click.echo("5. Validate configuration:")
        click.echo("   dtk validate metrics/example_metric.yaml")
        click.echo()

        click.echo("6. Run your first check:")
        click.echo("   dtk run metrics/example_metric.yaml")
        click.echo()

        click.echo("📚 Documentation: https://github.com/alexeiveselov92/detectk")
        click.echo()

    except Exception as e:
        click.echo(f"❌ Error creating project: {e}", err=True)
        logger.exception("Project initialization failed")
        sys.exit(1)


@cli.command("load-history")
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be loaded without actually loading data",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force reload all data (ignore existing checkpoints)",
)
@click.option(
    "--skip-detection",
    is_flag=True,
    help="Skip running detectors (faster, only load raw data)",
)
def load_history(config_path: Path, dry_run: bool, force: bool, skip_detection: bool) -> None:
    """Load historical data for detector training (initial setup).

    This command bulk-loads historical data into storage for metrics that
    require historical window (e.g., MAD, Z-Score detectors need 30 days).

    By default, this command:
    1. Loads raw data into dtk_datapoints
    2. Runs detectors on each point
    3. Saves detection results to dtk_detections (no alerts sent!)

    This creates full detection history for AlertAnalyzer features
    (consecutive anomalies, cooldown logic, etc.).

    Use --skip-detection for faster loading if you only need raw data.

    The config must specify schedule.start_time and schedule.end_time.
    Data is loaded in batches (schedule.batch_load_days) for efficiency.

    IMPORTANT: Set alerter.enabled=false to skip alerts during bulk load!

    CONFIG_PATH: Path to YAML configuration file

    \b
    Examples:
        # Load historical data with detection
        dtk load-history configs/sessions_historical.yaml

        # Fast load (raw data only, no detection)
        dtk load-history configs/sessions_historical.yaml --skip-detection

        # Dry run to see what would be loaded
        dtk load-history configs/sessions_historical.yaml --dry-run

        # Force reload (ignore existing data)
        dtk load-history configs/sessions_historical.yaml --force
    """
    from datetime import timedelta
    from detectk.registry import CollectorRegistry, StorageRegistry

    try:
        # Check if tqdm is available
        try:
            from tqdm import tqdm
            has_tqdm = True
        except ImportError:
            has_tqdm = False
            click.echo("⚠️  Install tqdm for progress bar: pip install tqdm")
            click.echo()

        click.echo(f"📥 Loading historical data: {config_path}")
        click.echo()

        # Load config
        loader = ConfigLoader()
        config = loader.load_file(str(config_path))

        # Validate schedule config
        if not config.schedule:
            click.echo("❌ Error: No schedule configuration found", err=True)
            click.echo("   Add schedule with start_time and end_time", err=True)
            sys.exit(1)

        if not config.schedule.start_time or not config.schedule.end_time:
            click.echo("❌ Error: schedule.start_time and schedule.end_time are required", err=True)
            click.echo("   These define the time range for historical load", err=True)
            sys.exit(1)

        if not config.schedule.interval:
            click.echo("❌ Error: schedule.interval is required", err=True)
            sys.exit(1)

        # Parse configuration
        from datetime import datetime as dt

        # Parse datetime strings
        start_time = dt.fromisoformat(config.schedule.start_time)
        end_time = dt.fromisoformat(config.schedule.end_time)
        interval_str = config.schedule.interval
        batch_days = config.schedule.batch_load_days or 30

        # Parse interval string
        interval_parts = interval_str.split()
        if len(interval_parts) != 2:
            click.echo(f"❌ Error: Invalid interval format: {interval_str}", err=True)
            click.echo("   Expected format: '10 minutes', '1 hour', etc.", err=True)
            sys.exit(1)

        interval_value = int(interval_parts[0])
        interval_unit = interval_parts[1].lower()

        if "minute" in interval_unit:
            interval_delta = timedelta(minutes=interval_value)
        elif "hour" in interval_unit:
            interval_delta = timedelta(hours=interval_value)
        elif "day" in interval_unit:
            interval_delta = timedelta(days=interval_value)
        else:
            click.echo(f"❌ Error: Unsupported interval unit: {interval_unit}", err=True)
            sys.exit(1)

        # Calculate batches
        batch_delta = timedelta(days=batch_days)
        total_duration = end_time - start_time
        num_batches = int((total_duration.total_seconds() / batch_delta.total_seconds())) + 1

        # Calculate estimated points
        points_per_batch = int((batch_delta.total_seconds() / interval_delta.total_seconds()))
        total_points_estimate = int((total_duration.total_seconds() / interval_delta.total_seconds()))

        # Display summary
        click.echo("=" * 70)
        click.echo("LOAD PLAN")
        click.echo("=" * 70)
        click.echo(f"Metric: {config.name}")
        click.echo(f"Time range: {start_time} → {end_time}")
        click.echo(f"Duration: {total_duration.days} days")
        click.echo(f"Interval: {interval_str}")
        click.echo(f"Batch size: {batch_days} days")
        click.echo(f"Number of batches: {num_batches}")
        click.echo(f"Estimated points per batch: ~{points_per_batch:,}")
        click.echo(f"Estimated total points: ~{total_points_estimate:,}")
        click.echo(f"Run detection: {'No (--skip-detection)' if skip_detection else 'Yes'}")
        click.echo()

        # Warn if alerter is enabled
        if config.alerter and config.alerter.enabled:
            click.echo("⚠️  WARNING: alerter.enabled=true - alerts will be sent!")
            click.echo("   Recommendation: Set alerter.enabled=false for historical loads")
            click.echo()
            if not click.confirm("Continue anyway?"):
                sys.exit(0)

        if dry_run:
            click.echo("=" * 70)
            click.echo("BATCHES (DRY RUN)")
            click.echo("=" * 70)
            batch_start = start_time
            for i in range(num_batches):
                batch_end = min(batch_start + batch_delta, end_time)
                batch_points = int(((batch_end - batch_start).total_seconds() / interval_delta.total_seconds()))
                click.echo(f"Batch {i+1}/{num_batches}: {batch_start} → {batch_end} (~{batch_points:,} points)")
                batch_start = batch_end

                if batch_start >= end_time:
                    break

            click.echo()
            click.echo("🏃 Dry run complete - no data was loaded")
            return

        # Get collector
        collector_class = CollectorRegistry.get(config.collector.type)
        collector = collector_class(config.collector.params)

        # Get storage (required for bulk load)
        if not config.storage.enabled:
            click.echo("❌ Error: storage.enabled=false", err=True)
            click.echo("   Storage is required for historical data loading", err=True)
            sys.exit(1)

        storage_type = config.storage.type or config.collector.type
        storage_class = StorageRegistry.get(storage_type)
        storage = storage_class(config.storage.params)

        # Prepare detectors if not skipping detection
        detectors_info = []
        if not skip_detection:
            from detectk.registry import DetectorRegistry

            detector_configs = config.get_detectors()
            for detector_config in detector_configs:
                try:
                    detector_class = DetectorRegistry.get(detector_config.type)
                    detector = detector_class(storage=storage, **detector_config.params)
                    detectors_info.append({
                        "config": detector_config,
                        "detector": detector,
                    })
                except Exception as e:
                    click.echo(f"⚠️  Warning: Could not initialize detector {detector_config.type}: {e}")
                    click.echo(f"   Continuing without this detector...")

            if not detectors_info:
                click.echo("⚠️  Warning: No detectors initialized, detection will be skipped")
                skip_detection = True

        # Check existing data (checkpoint)
        last_loaded = None
        if not force:
            last_loaded = storage.get_last_loaded_timestamp(config.name)
            if last_loaded:
                click.echo(f"📍 Checkpoint found: last loaded data at {last_loaded}")
                click.echo(f"   Resuming from {last_loaded + interval_delta}")
                click.echo()

        # Load batches
        click.echo("=" * 70)
        click.echo("LOADING BATCHES")
        click.echo("=" * 70)

        batch_start = start_time
        if last_loaded and not force:
            # Resume from checkpoint
            batch_start = last_loaded + interval_delta
            if batch_start >= end_time:
                click.echo("✅ All data already loaded (checkpoint at end_time)")
                return

        total_points_loaded = 0
        batches_completed = 0

        # Create progress bar if tqdm available
        if has_tqdm:
            progress_bar = tqdm(total=num_batches, desc="Loading batches", unit="batch")

        batch_num = 1
        while batch_start < end_time:
            batch_end = min(batch_start + batch_delta, end_time)

            try:
                # Collect data for batch
                if not has_tqdm:
                    click.echo(f"Batch {batch_num}/{num_batches}: {batch_start} → {batch_end}")

                datapoints = collector.collect_bulk(
                    period_start=batch_start,
                    period_finish=batch_end,
                )

                # Save to storage
                if datapoints:
                    storage.save_datapoints_bulk(config.name, datapoints)
                    total_points_loaded += len(datapoints)

                    if not has_tqdm:
                        click.echo(f"  ✓ Loaded {len(datapoints):,} points")

                    # Run detection on each point if not skipping
                    if not skip_detection and detectors_info:
                        detections_saved = 0
                        for datapoint in datapoints:
                            for detector_info in detectors_info:
                                try:
                                    detector = detector_info["detector"]
                                    detector_config = detector_info["config"]

                                    # Run detection
                                    detection = detector.detect(
                                        metric_name=config.name,
                                        value=datapoint.value,
                                        timestamp=datapoint.timestamp,
                                    )

                                    # Save detection to dtk_detections
                                    # Check if storage has save_detections param enabled
                                    if config.storage.params.get("save_detections", True):
                                        storage.save_detection(
                                            metric_name=config.name,
                                            detection=detection,
                                            detector_id=detector_config.id,
                                            alert_sent=False,  # Never alert during historical load
                                            alert_reason=None,
                                            alerter_type=None,
                                        )
                                        detections_saved += 1

                                except Exception as e:
                                    # Log but don't fail the entire load
                                    logger.debug(f"Detection failed for point {datapoint.timestamp}: {e}")

                        if not has_tqdm and detections_saved > 0:
                            click.echo(f"  ✓ Saved {detections_saved:,} detections")

                batches_completed += 1

                if has_tqdm:
                    progress_bar.update(1)
                    progress_bar.set_postfix({"points": f"{total_points_loaded:,}"})

            except Exception as e:
                if has_tqdm:
                    progress_bar.close()
                click.echo()
                click.echo(f"❌ Error loading batch {batch_num}: {e}", err=True)
                click.echo(f"   Last successful: {batch_start}")
                click.echo(f"   You can resume with the same command (checkpoint saved)")
                sys.exit(1)

            batch_start = batch_end
            batch_num += 1

        if has_tqdm:
            progress_bar.close()

        # Clean up
        if hasattr(collector, "close"):
            collector.close()
        if hasattr(storage, "close"):
            storage.close()

        # Summary
        click.echo()
        click.echo("=" * 70)
        click.echo("SUMMARY")
        click.echo("=" * 70)
        click.echo(f"✅ Historical load complete!")
        click.echo(f"   Batches completed: {batches_completed}/{num_batches}")
        click.echo(f"   Total points loaded: {total_points_loaded:,}")
        click.echo(f"   Time range: {start_time} → {end_time}")
        if not skip_detection and detectors_info:
            num_detectors = len(detectors_info)
            total_detections = total_points_loaded * num_detectors
            click.echo(f"   Detections saved: ~{total_detections:,} ({num_detectors} detector(s))")
        elif skip_detection:
            click.echo(f"   Detections: Skipped (--skip-detection)")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"1. Update config to use production schedule (remove start_time/end_time)")
        click.echo(f"2. Set alerter.enabled=true")
        if skip_detection:
            click.echo(f"3. Optional: Re-run without --skip-detection to build detection history")
            click.echo(f"4. Run production monitoring:")
        else:
            click.echo(f"3. Run production monitoring:")
        click.echo(f"   dtk run {config_path}")
        click.echo()

    except ConfigurationError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("load-history failed")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--tags",
    "-t",
    multiple=True,
    help="Run only metrics with specified tags (can be used multiple times)",
)
@click.option(
    "--exclude-tags",
    "-e",
    multiple=True,
    help="Exclude metrics with specified tags (can be used multiple times)",
)
@click.option(
    "--match-all",
    is_flag=True,
    help="Require ALL specified tags to match (default: match ANY tag)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would run without actually running",
)
@click.option(
    "--parallel",
    "-p",
    is_flag=True,
    help="Run metrics in parallel (experimental)",
)
def run_tagged(
    directory: Path,
    tags: tuple[str, ...],
    exclude_tags: tuple[str, ...],
    match_all: bool,
    dry_run: bool,
    parallel: bool,
) -> None:
    """Run multiple metrics filtered by tags.

    DIRECTORY: Directory to search for metric configs (default: current directory)

    \b
    Examples:
        # Run all metrics tagged with 'critical'
        dtk run-tagged --tags critical

        # Run metrics with 'revenue' OR 'orders' tags
        dtk run-tagged --tags revenue --tags orders

        # Run metrics with BOTH 'hourly' AND 'critical' tags
        dtk run-tagged --tags hourly --tags critical --match-all

        # Run all except 'experimental' metrics
        dtk run-tagged --exclude-tags experimental

        # Dry run to see what would be executed
        dtk run-tagged --tags critical --dry-run

        # Run in parallel (experimental)
        dtk run-tagged --tags critical --parallel
    """
    try:
        if not tags and not exclude_tags:
            click.echo("❌ Error: Specify at least one tag with --tags or --exclude-tags", err=True)
            sys.exit(1)

        # Find all YAML files
        yaml_files = list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))

        if not yaml_files:
            click.echo(f"⚠️  No YAML files found in {directory}")
            sys.exit(0)

        # Load and filter configs by tags
        loader = ConfigLoader()
        matched_configs: list[tuple[Path, Any]] = []

        click.echo(f"🔍 Searching for metrics in {directory}")
        click.echo(f"   Tags: {', '.join(tags) if tags else '(none)'}")
        if exclude_tags:
            click.echo(f"   Exclude: {', '.join(exclude_tags)}")
        click.echo(f"   Match mode: {'ALL tags' if match_all else 'ANY tag'}")
        click.echo()

        for yaml_file in yaml_files:
            try:
                config = loader.load(str(yaml_file))

                # Check exclude tags first
                if exclude_tags:
                    metric_tags_set = set(config.tags) if config.tags else set()
                    if metric_tags_set & set(exclude_tags):  # Intersection
                        logger.debug(f"Excluding {yaml_file.name}: has excluded tag")
                        continue

                # Check include tags
                if tags:
                    metric_tags_set = set(config.tags) if config.tags else set()
                    required_tags_set = set(tags)

                    if match_all:
                        # ALL tags must match
                        if not required_tags_set.issubset(metric_tags_set):
                            continue
                    else:
                        # ANY tag must match
                        if not (required_tags_set & metric_tags_set):
                            continue

                matched_configs.append((yaml_file, config))

            except ConfigurationError as e:
                logger.debug(f"Skipping invalid config {yaml_file}: {e}")
                continue
            except Exception as e:
                logger.debug(f"Skipping {yaml_file}: {e}")
                continue

        if not matched_configs:
            click.echo("⚠️  No metrics matched the tag filter")
            sys.exit(0)

        # Display matched metrics
        click.echo(f"📊 Found {len(matched_configs)} matching metric(s):")
        click.echo()
        for yaml_file, config in matched_configs:
            tags_str = f"[{', '.join(config.tags)}]" if config.tags else "[no tags]"
            click.echo(f"  ✓ {config.name:30s} {tags_str}")
            click.echo(f"    {yaml_file}")

        if dry_run:
            click.echo()
            click.echo("🏃 Dry run mode - no metrics were executed")
            sys.exit(0)

        # Execute metrics
        click.echo()
        click.echo("=" * 70)
        click.echo("EXECUTING METRICS")
        click.echo("=" * 70)
        click.echo()

        checker = MetricCheck()
        success_count = 0
        error_count = 0
        results: list[tuple[str, Any, list[str]]] = []

        if parallel:
            click.echo("⚡ Parallel execution mode (experimental)")
            click.echo()
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_config = {
                    executor.submit(checker.execute, str(yaml_file)): (yaml_file, config)
                    for yaml_file, config in matched_configs
                }

                for future in concurrent.futures.as_completed(future_to_config):
                    yaml_file, config = future_to_config[future]
                    try:
                        result = future.result()
                        results.append((config.name, result, []))
                        success_count += 1
                        click.echo(f"✅ {config.name}")
                    except Exception as e:
                        results.append((config.name, None, [str(e)]))
                        error_count += 1
                        click.echo(f"❌ {config.name}: {e}")
        else:
            # Sequential execution
            for yaml_file, config in matched_configs:
                click.echo(f"Running: {config.name}")
                try:
                    result = checker.execute(str(yaml_file))
                    results.append((config.name, result, result.errors if result.errors else []))

                    if result.errors:
                        error_count += 1
                        click.echo(f"  ⚠️  Completed with errors")
                        for error in result.errors:
                            click.echo(f"     - {error}")
                    else:
                        success_count += 1
                        click.echo(f"  ✅ Success")

                    if result.alert_sent:
                        click.echo(f"  ✉️  Alert sent: {result.alert_reason}")

                except Exception as e:
                    error_count += 1
                    results.append((config.name, None, [str(e)]))
                    click.echo(f"  ❌ Failed: {e}")

                click.echo()

        # Summary
        click.echo("=" * 70)
        click.echo("SUMMARY")
        click.echo("=" * 70)
        click.echo(f"Total metrics: {len(matched_configs)}")
        click.echo(f"Success: {success_count}")
        click.echo(f"Errors: {error_count}")
        click.echo()

        if error_count > 0:
            click.echo("⚠️  Some metrics failed")
            sys.exit(1)
        else:
            click.echo("✅ All metrics completed successfully")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("run-tagged failed")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
