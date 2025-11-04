"""Command-line interface for Debian Repository Manager.

This module provides the main CLI entry point using Click.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

import click

from debrepomanager.aptly import AptlyError, AptlyManager
from debrepomanager.config import Config, ConfigError
from debrepomanager.utils import find_deb_files, setup_logging

logger = logging.getLogger(__name__)


def _collect_package_files(
    packages: tuple, package_dir: Optional[str], verbose: bool
) -> List[str]:
    """Collect package files from arguments.

    Args:
        packages: Tuple of package file paths
        package_dir: Optional directory containing packages
        verbose: Whether to print verbose messages

    Returns:
        List of package file paths

    Raises:
        click.ClickException: If package collection fails
    """
    pkg_files: List[str] = list(packages)

    if package_dir:
        try:
            found_files = find_deb_files(package_dir, recursive=True)
            pkg_files.extend(found_files)
            if verbose:
                click.echo(f"Found {len(found_files)} package(s) in {package_dir}")
        except (FileNotFoundError, ValueError) as e:
            raise click.ClickException(str(e))

    if not pkg_files:
        raise click.ClickException(
            "No packages specified. Use --packages or --package-dir"
        )

    return pkg_files


def _ensure_repo_exists(
    manager: AptlyManager, codename: str, component: str, force: bool, auto_create: bool
) -> None:
    """Ensure repository exists, creating if needed.

    Args:
        manager: AptlyManager instance
        codename: Distribution codename
        component: Repository component
        force: Whether to force creation
        auto_create: Whether auto-create is enabled

    Raises:
        click.ClickException: If repo doesn't exist and can't be created
    """
    if not manager.repo_exists(codename, component):
        if force or auto_create:
            click.echo(f"Repository {component} doesn't exist, creating...")
            manager.create_repo(codename, component)
            click.echo("✓ Repository created")
        else:
            raise click.ClickException(
                f"Repository {codename}/{component} doesn't exist. "
                "Use --force to create or enable auto_create in config."
            )


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (DEBUG level)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Simulate operations without making changes",
)
@click.pass_context
def cli(
    ctx: click.Context, config: Optional[str], verbose: bool, dry_run: bool
) -> None:
    """Debian Repository Manager - manage Debian-like repositories with aptly.

    Examples:

        \b
        # Add packages to repository
        repomanager add --codename bookworm --component jethome-tools --packages *.deb

        \b
        # Create new repository
        repomanager create-repo --codename noble --component jethome-armbian

        \b
        # List repositories
        repomanager list --codename bookworm
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    ctx.obj["logger"] = setup_logging(level=log_level)
    ctx.obj["verbose"] = verbose
    ctx.obj["dry_run"] = dry_run

    # Load configuration
    try:
        ctx.obj["config"] = Config(config)
        if verbose:
            click.echo(f"Loaded configuration from: {config or 'default locations'}")
    except ConfigError as e:
        click.echo(f"Error: Configuration error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--codename",
    required=True,
    help="Distribution codename (e.g., bookworm, noble, trixie)",
)
@click.option(
    "--component",
    required=True,
    help="Repository component (e.g., jethome-tools, jethome-armbian)",
)
@click.option(
    "--packages",
    multiple=True,
    type=click.Path(exists=True),
    help="Package files to add (can be specified multiple times)",
)
@click.option(
    "--package-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing .deb packages (searched recursively)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Create repository if it doesn't exist (even if auto_create is disabled)",
)
@click.pass_context
def add(
    ctx: click.Context,
    codename: str,
    component: str,
    packages: tuple,
    package_dir: Optional[str],
    force: bool,
) -> None:
    """Add packages to repository with atomic snapshot publication.

    Examples:

        \b
        # Add specific packages
        repomanager add --codename bookworm --component jethome-tools \\
            --packages pkg1.deb --packages pkg2.deb

        \b
        # Add all packages from directory
        repomanager add --codename bookworm --component jethome-tools \\
            --package-dir /path/to/packages/

        \b
        # Force create repository if doesn't exist
        repomanager add --codename bookworm --component jethome-tools \\
            --package-dir /path/to/packages/ --force
    """
    config: Config = ctx.obj["config"]
    dry_run: bool = ctx.obj["dry_run"]
    verbose: bool = ctx.obj["verbose"]

    # Collect package files
    try:
        pkg_files = _collect_package_files(packages, package_dir, verbose)
    except click.ClickException:
        raise

    if verbose:
        click.echo(f"Adding {len(pkg_files)} package(s) to {codename}/{component}")

    # Dry run mode
    if dry_run:
        click.echo("Dry-run mode: No changes will be made")
        click.echo(f"Would add {len(pkg_files)} package(s):")
        for pkg in pkg_files:
            click.echo(f"  - {Path(pkg).name}")
        return

    # Add packages
    try:
        manager = AptlyManager(config)
        _ensure_repo_exists(
            manager, codename, component, force, config.auto_create_repos
        )

        click.echo(f"Adding {len(pkg_files)} package(s)...")
        manager.add_packages(codename, component, pkg_files)

        click.echo("✓ Packages added successfully")
        click.echo(f"Repository: {codename}/{component}")

    except click.ClickException:
        raise
    except (AptlyError, ConfigError, FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        logger.exception("Unexpected error in add command")
        sys.exit(99)


@cli.command("create-repo")
@click.option(
    "--codename",
    required=True,
    help="Distribution codename (e.g., bookworm, noble)",
)
@click.option(
    "--component",
    required=True,
    help="Repository component (e.g., jethome-tools)",
)
@click.option(
    "--architectures",
    multiple=True,
    help="Architectures to support (default: from config)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Recreate repository if it already exists",
)
@click.pass_context
def create_repo(
    ctx: click.Context,
    codename: str,
    component: str,
    architectures: tuple,
    force: bool,
) -> None:
    """Create new repository.

    Examples:

        \b
        # Create repository with default architectures
        repomanager create-repo --codename bookworm --component jethome-tools

        \b
        # Create with specific architectures
        repomanager create-repo --codename bookworm --component test \\
            --architectures amd64 --architectures arm64

        \b
        # Force recreate if exists
        repomanager create-repo --codename bookworm --component test --force
    """
    config: Config = ctx.obj["config"]
    dry_run: bool = ctx.obj["dry_run"]

    if dry_run:
        click.echo("Dry-run mode: No changes will be made")
        click.echo(f"Would create repository: {codename}/{component}")
        if architectures:
            click.echo(f"Architectures: {', '.join(architectures)}")
        return

    try:
        manager = AptlyManager(config)

        archs = list(architectures) if architectures else None

        if ctx.obj["verbose"]:
            click.echo(f"Creating repository {codename}/{component}...")

        manager.create_repo(codename, component, architectures=archs, force=force)

        click.echo(f"✓ Repository created: {codename}/{component}")

    except ValueError as e:
        # Repository already exists
        click.echo(f"Error: {e}", err=True)
        click.echo("Hint: Use --force to recreate", err=True)
        sys.exit(1)
    except (AptlyError, ConfigError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("delete-repo")
@click.option(
    "--codename",
    required=True,
    help="Distribution codename",
)
@click.option(
    "--component",
    required=True,
    help="Repository component",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm deletion (required for safety)",
)
@click.pass_context
def delete_repo(
    ctx: click.Context,
    codename: str,
    component: str,
    confirm: bool,
) -> None:
    """Delete repository and all its snapshots.

    Examples:

        \b
        # Delete repository (requires --confirm)
        repomanager delete-repo --codename bookworm --component old-repo --confirm
    """
    config: Config = ctx.obj["config"]
    dry_run: bool = ctx.obj["dry_run"]

    if dry_run:
        click.echo("Dry-run mode: No changes will be made")
        click.echo(f"Would delete repository: {codename}/{component}")
        return

    if not confirm:
        click.echo("Error: Repository deletion requires --confirm flag", err=True)
        click.echo(f"To delete {codename}/{component}, run:", err=True)
        click.echo(
            f"  repomanager delete-repo --codename {codename} --component {component} --confirm",
            err=True,
        )
        sys.exit(1)

    try:
        manager = AptlyManager(config)

        # Check if repository exists BEFORE confirmation prompt
        if not manager.repo_exists(codename, component):
            click.echo(
                f"Error: Repository {codename}/{component} doesn't exist", err=True
            )
            sys.exit(1)

        # Additional confirmation prompt
        click.echo(f"⚠️  WARNING: This will delete repository {codename}/{component}")
        click.echo("⚠️  This action cannot be undone!")

        if not click.confirm("Are you sure you want to continue?"):
            click.echo("Cancelled.")
            sys.exit(0)

        click.echo(f"Deleting repository {codename}/{component}...")
        manager.delete_repo(codename, component)

        click.echo(f"✓ Repository deleted: {codename}/{component}")

    except (AptlyError, ConfigError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("list")
@click.option(
    "--codename",
    help="Filter by distribution codename",
)
@click.option(
    "--component",
    help="Filter by component",
)
@click.pass_context
def list_repos(
    ctx: click.Context,
    codename: Optional[str],
    component: Optional[str],
) -> None:
    """List repositories and packages.

    Examples:

        \b
        # List all repositories
        repomanager list

        \b
        # List repos for specific codename
        repomanager list --codename bookworm

        \b
        # List packages in specific component
        repomanager list --codename bookworm --component jethome-tools
    """
    config: Config = ctx.obj["config"]

    try:
        manager = AptlyManager(config)

        if codename and component:
            # List packages in specific component
            if not manager.repo_exists(codename, component):
                click.echo(f"Repository {codename}/{component} doesn't exist", err=True)
                sys.exit(1)

            packages = manager.list_packages(codename, component)

            click.echo(f"Repository: {codename}/{component}")
            click.echo(f"Packages: {len(packages)}")
            click.echo()

            if packages:
                for pkg in packages:
                    click.echo(f"  {pkg}")
            else:
                click.echo("  (empty)")

        else:
            # List repositories
            if codename:
                repos = manager.list_repos(codename)
                click.echo(f"Repositories for {codename}:")
            else:
                repos = manager.list_repos()
                click.echo("All repositories:")

            click.echo(f"Total: {len(repos)}")
            click.echo()

            if repos:
                for repo in repos:
                    click.echo(f"  {repo}")
            else:
                click.echo("  (none)")

    except (AptlyError, ConfigError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
