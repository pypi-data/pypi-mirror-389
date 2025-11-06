"""Command-line interface for market_data_core configuration management.

Provides commands to:
- Validate configuration files
- Inspect loaded configuration
- Test environment variable resolution
"""

import json
import sys
from pathlib import Path

import click
from pydantic import ValidationError

from .configs.loader import load_config


@click.group()
@click.version_option()
def cli() -> None:
    """Market Data Core - Configuration Management CLI."""
    pass


@cli.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--profile",
    type=click.Choice(["dev", "staging", "prod"]),
    default=None,
    help="Profile to use (overrides config file)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation information",
)
def validate(config_path: Path, profile: str | None, verbose: bool) -> None:
    """Validate a configuration file.

    CONFIG_PATH: Path to the configuration YAML file to validate.

    Examples:
        market-data-core validate configs/prices.yaml
        market-data-core validate configs/prices.yaml --profile prod
    """
    try:
        cfg = load_config(config_path, profile_override=profile)

        click.echo(click.style("✅ Configuration is valid", fg="green", bold=True))
        click.echo(f"   Profile: {cfg.profile}")
        click.echo(f"   Providers: {len(cfg.providers.root)}")
        click.echo(f"   Storage targets: {len(cfg.storage.root)}")
        click.echo(f"   Datasets: {len(cfg.datasets.root)}")
        click.echo(f"   Jobs: {len(cfg.jobs.root)}")

        if verbose:
            click.echo("\n" + "=" * 60)
            click.echo("Providers:")
            for name, provider in cfg.providers.root.items():
                click.echo(f"  - {name} ({provider.type})")

            click.echo("\nDatasets:")
            for name, dataset in cfg.datasets.root.items():
                click.echo(
                    f"  - {name}: {dataset.provider} / {dataset.interval} / {dataset.symbols}"
                )

            click.echo("\nJobs:")
            for name, job in cfg.jobs.root.items():
                click.echo(f"  - {name}: {job.mode} / {job.dataset}")

    except FileNotFoundError as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red", bold=True), err=True)
        sys.exit(1)

    except ValidationError as e:
        click.echo(click.style("❌ Configuration validation failed", fg="red", bold=True), err=True)
        click.echo("\nValidation errors:", err=True)
        for error in e.errors():
            loc = " → ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            click.echo(f"  • {loc}: {msg}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red", bold=True), err=True)
        if verbose:
            import traceback

            click.echo("\nTraceback:", err=True)
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--profile",
    type=click.Choice(["dev", "staging", "prod"]),
    default=None,
    help="Profile to use (overrides config file)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
def inspect(config_path: Path, profile: str | None, output_format: str) -> None:
    """Inspect a loaded configuration (with env vars resolved).

    CONFIG_PATH: Path to the configuration YAML file to inspect.

    Examples:
        market-data-core inspect configs/prices.yaml
        market-data-core inspect configs/prices.yaml --profile prod --format yaml
    """
    try:
        cfg = load_config(config_path, profile_override=profile)

        # Convert to dict for output
        cfg_dict = cfg.model_dump(mode="json")

        if output_format == "json":
            click.echo(json.dumps(cfg_dict, indent=2))
        else:  # yaml
            import yaml

            click.echo(yaml.dump(cfg_dict, default_flow_style=False, sort_keys=False))

    except FileNotFoundError as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red", bold=True), err=True)
        sys.exit(1)

    except ValidationError as e:
        click.echo(click.style("❌ Configuration validation failed", fg="red", bold=True), err=True)
        for error in e.errors():
            loc = " → ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            click.echo(f"  • {loc}: {msg}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red", bold=True), err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
