"""Metric selector resolution for CLI commands.

This module provides functionality to resolve metric configurations based on
various selector patterns (paths, tags, globs, etc.).

Inspired by dbt's selector syntax but adapted for DetectK use cases.
"""

from pathlib import Path
from typing import Any
import fnmatch
import logging

from detectk.config.loader import ConfigLoader
from detectk.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def resolve_metrics(
    config_path: str | None = None,
    select: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] | None = None,
    base_path: Path | None = None,
) -> list[Path]:
    """Resolve metric configuration files based on selectors.

    Args:
        config_path: Optional direct path to config file or directory
        select: Tuple of selector patterns (tag:name, glob, metric_name, etc.)
        exclude: Tuple of exclude patterns (same syntax as select)
        base_path: Base directory to search for metrics (default: ./metrics/)

    Returns:
        List of resolved config file paths

    Raises:
        ConfigurationError: If no path/selector provided or no metrics found

    Selector Syntax:
        - tag:TAG_NAME          -> Filter by tag
        - type:COLLECTOR_TYPE   -> Filter by collector type
        - glob_pattern          -> Glob pattern matching
        - metric_name           -> Exact metric name match
        - path/to/file.yaml     -> Direct file path
        - path/to/dir/          -> All configs in directory

    Examples:
        >>> # Single file
        >>> resolve_metrics(config_path="configs/sessions.yaml")
        [Path("configs/sessions.yaml")]

        >>> # Directory
        >>> resolve_metrics(config_path="configs/")
        [Path("configs/sessions.yaml"), Path("configs/revenue.yaml")]

        >>> # By tag
        >>> resolve_metrics(select=("tag:critical",))
        [Path("metrics/sessions.yaml"), Path("metrics/orders.yaml")]

        >>> # Multiple selectors (OR logic)
        >>> resolve_metrics(select=("tag:critical", "tag:hourly"))
        [...]

        >>> # With exclusion
        >>> resolve_metrics(select=("tag:critical",), exclude=("tag:experimental",))
        [...]

        >>> # Glob pattern
        >>> resolve_metrics(select=("sessions_*",))
        [Path("metrics/sessions_10min.yaml"), Path("metrics/sessions_hourly.yaml")]
    """
    # Validate arguments
    if not config_path and not select:
        raise ConfigurationError(
            "Either CONFIG_PATH or --select must be specified.\n\n"
            "Examples:\n"
            "  dtk run configs/sessions.yaml\n"
            "  dtk run configs/\n"
            "  dtk run --select tag:critical\n"
            "  dtk run --select 'sessions_*'"
        )

    if config_path and select:
        raise ConfigurationError(
            "Cannot specify both CONFIG_PATH and --select.\n"
            "Use one or the other."
        )

    # Determine base path for metrics search
    if base_path is None:
        base_path = Path.cwd() / "metrics"

    # Case 1: Direct path provided
    if config_path:
        path = Path(config_path)

        # Single file
        if path.is_file():
            return [path]

        # Directory - find all yaml files
        if path.is_dir():
            configs = _find_configs_in_directory(path)
            if not configs:
                raise ConfigurationError(f"No metric configs found in directory: {path}")
            return configs

        # Path doesn't exist
        raise ConfigurationError(f"Path not found: {path}")

    # Case 2: Selectors provided
    if select:
        # Find all metric configs in base path
        if not base_path.exists():
            raise ConfigurationError(
                f"Metrics directory not found: {base_path}\n\n"
                f"Initialize a project with: dtk init-project"
            )

        all_configs = _find_configs_in_directory(base_path)
        if not all_configs:
            raise ConfigurationError(
                f"No metric configs found in: {base_path}\n\n"
                f"Create a metric with: dtk init metrics/my_metric.yaml"
            )

        # Apply selectors
        selected_configs = _apply_selectors(all_configs, select, base_path)

        # Apply exclusions
        if exclude:
            selected_configs = _apply_exclusions(selected_configs, exclude, base_path)

        if not selected_configs:
            raise ConfigurationError(
                f"No metrics matched selectors.\n"
                f"Select: {', '.join(select)}\n"
                f"Exclude: {', '.join(exclude) if exclude else 'none'}"
            )

        return selected_configs

    # Should not reach here
    raise ConfigurationError("Invalid selector configuration")


def _find_configs_in_directory(directory: Path) -> list[Path]:
    """Find all .yaml/.yml files recursively in directory.

    Args:
        directory: Directory to search

    Returns:
        List of config file paths, sorted
    """
    configs = []
    configs.extend(directory.glob("**/*.yaml"))
    configs.extend(directory.glob("**/*.yml"))

    # Exclude templates
    configs = [c for c in configs if not c.name.endswith(".template")]

    return sorted(set(configs))


def _apply_selectors(
    configs: list[Path],
    selectors: tuple[str, ...],
    base_path: Path,
) -> list[Path]:
    """Apply selector patterns to filter configs (OR logic).

    Args:
        configs: List of config paths to filter
        selectors: Selector patterns
        base_path: Base path for metric search

    Returns:
        Filtered list of configs (OR logic - any selector matches)
    """
    if not selectors:
        return configs

    loader = ConfigLoader()
    matched_configs = set()

    for selector in selectors:
        # Parse selector
        selector_type, selector_value = _parse_selector(selector)

        for config_path in configs:
            # Check if already matched
            if config_path in matched_configs:
                continue

            try:
                # Selector type: tag:TAG_NAME
                if selector_type == "tag":
                    config = loader.load_file(str(config_path), lenient=True)
                    if config.tags and selector_value in config.tags:
                        matched_configs.add(config_path)
                        continue

                # Selector type: type:COLLECTOR_TYPE
                elif selector_type == "type":
                    config = loader.load_file(str(config_path), lenient=True)
                    if config.collector.type == selector_value:
                        matched_configs.add(config_path)
                        continue

                # Selector type: metric name or glob pattern
                elif selector_type == "pattern":
                    # Try exact metric name match
                    config = loader.load_file(str(config_path), lenient=True)
                    if config.name == selector_value:
                        matched_configs.add(config_path)
                        continue

                    # Try glob pattern on metric name
                    if fnmatch.fnmatch(config.name, selector_value):
                        matched_configs.add(config_path)
                        continue

                    # Try glob pattern on file path (relative to base_path)
                    try:
                        rel_path = config_path.relative_to(base_path)
                        if fnmatch.fnmatch(str(rel_path), selector_value):
                            matched_configs.add(config_path)
                            continue
                    except ValueError:
                        # Not relative to base_path
                        pass

            except ConfigurationError:
                # Skip invalid configs
                logger.debug(f"Skipping invalid config: {config_path}")
                continue
            except Exception as e:
                # Skip configs that fail to load
                logger.debug(f"Error loading {config_path}: {e}")
                continue

    return sorted(matched_configs)


def _apply_exclusions(
    configs: list[Path],
    exclusions: tuple[str, ...],
    base_path: Path,
) -> list[Path]:
    """Apply exclusion patterns to filter out configs.

    Args:
        configs: List of config paths to filter
        exclusions: Exclusion patterns (same syntax as selectors)
        base_path: Base path for metric search

    Returns:
        Filtered list with excluded configs removed
    """
    if not exclusions:
        return configs

    # Get configs that match exclusion patterns
    excluded_configs = set(_apply_selectors(configs, exclusions, base_path))

    # Remove excluded configs
    return [c for c in configs if c not in excluded_configs]


def _parse_selector(selector: str) -> tuple[str, str]:
    """Parse selector string into type and value.

    Args:
        selector: Selector string (e.g., "tag:critical", "sessions_*")

    Returns:
        Tuple of (selector_type, selector_value)
        selector_type: "tag", "type", or "pattern"
        selector_value: The value to match

    Examples:
        >>> _parse_selector("tag:critical")
        ("tag", "critical")

        >>> _parse_selector("type:clickhouse")
        ("type", "clickhouse")

        >>> _parse_selector("sessions_*")
        ("pattern", "sessions_*")
    """
    # Check for prefix selectors
    if ":" in selector:
        parts = selector.split(":", 1)
        selector_type = parts[0].lower()
        selector_value = parts[1]

        if selector_type in ("tag", "type"):
            return (selector_type, selector_value)

    # Default to pattern matching
    return ("pattern", selector)
