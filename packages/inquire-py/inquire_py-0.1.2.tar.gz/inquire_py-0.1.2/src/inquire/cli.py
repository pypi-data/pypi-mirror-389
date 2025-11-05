"""CLI commands for inquire."""

import asyncio
import shutil
import sys
from pathlib import Path
from typing import Optional

import click


@click.group()
def cli():
    """inquire - Intelligent inquiry with structured results."""
    pass


@cli.command()
@click.option(
    "--dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory containing .baml files (default: current directory)",
)
def init(dir: Optional[Path]):
    """Initialize BAML project and copy schema files.

    This command:
    1. Creates baml_schemas/ directory structure
    2. Runs 'baml init' to set up the project
    3. Copies all .baml files to baml_schemas/baml_src/
    4. Runs 'baml-cli generate' to create Python types
    """
    asyncio.run(_init_async(dir))


async def _init_async(source_dir: Optional[Path]):
    """Async implementation of init command."""
    source_dir = source_dir or Path.cwd()

    click.echo(f"🔍 Looking for .baml files in: {source_dir}")

    # Find all .baml files in the source directory
    baml_files = list(source_dir.glob("*.baml"))

    if not baml_files:
        click.secho(
            f"❌ No .baml files found in {source_dir}\n"
            "Create at least one .baml schema file first.",
            fg="red",
        )
        sys.exit(1)

    click.echo(f"✅ Found {len(baml_files)} .baml file(s):")
    for f in baml_files:
        click.echo(f"   - {f.name}")

    # Create baml_schemas directory
    baml_dir = source_dir / "baml_schemas"
    baml_src_dir = baml_dir / "baml_src"

    if baml_src_dir.exists():
        click.secho(
            f"⚠️  {baml_dir} already exists. Skipping baml init.",
            fg="yellow",
        )
    else:
        click.echo(f"\n📦 Initializing BAML project in {baml_dir}...")
        baml_dir.mkdir(parents=True, exist_ok=True)

        # Run baml init
        try:
            process = await asyncio.create_subprocess_exec(
                "baml",
                "init",
                cwd=baml_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                click.secho(f"❌ BAML init failed: {stderr.decode()}", fg="red")
                sys.exit(1)

            click.secho("✅ BAML project initialized", fg="green")
        except FileNotFoundError:
            click.secho("❌ 'baml' command not found", fg="red")
            click.echo("Install BAML CLI: npm install -g @boundaryml/baml")
            sys.exit(1)

    # Copy .baml files to baml_src
    click.echo(f"\n📋 Copying .baml files to {baml_src_dir}...")
    for baml_file in baml_files:
        dest = baml_src_dir / baml_file.name
        shutil.copy2(baml_file, dest)
        click.echo(f"   ✅ Copied {baml_file.name}")

    # Delete original .baml files to avoid duplication
    click.echo("\n🧹 Cleaning up original .baml files...")
    for baml_file in baml_files:
        baml_file.unlink()
        click.echo(f"   🗑️  Removed {baml_file.name}")

    # Run baml-cli generate
    click.echo("\n🔨 Generating Python types...")
    try:
        process = await asyncio.create_subprocess_exec(
            "baml-cli",
            "generate",
            "--client-type",
            "python/pydantic",
            cwd=baml_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            click.secho(f"❌ BAML generate failed: {stderr.decode()}", fg="red")
            sys.exit(1)
    except FileNotFoundError:
        click.secho("❌ 'baml-cli' command not found", fg="red")
        click.echo("Install BAML CLI: npm install -g @boundaryml/baml")
        sys.exit(1)

    click.secho("\n✨ Success! Your BAML project is ready.", fg="green", bold=True)
    click.echo("\nNext steps:")
    click.echo("  1. Import types: from baml_client.types import YourType")
    click.echo("  2. Import functions: from baml_client import b")
    click.echo("  3. Use inquire: await research(..., baml_function=b.YourFunction)")
    click.echo("\nProject structure:")
    click.echo(f"  {baml_dir}/")
    click.echo("    ├── baml_src/")
    for f in baml_files:
        click.echo(f"    │   ├── {f.name}")
    click.echo("    │   ├── clients.baml      # LLM configurations")
    click.echo("    │   └── generators.baml   # Code generation settings")
    click.echo("    └── baml_client/          # Generated Python types")
    click.echo("\nNote: Original .baml files have been moved to baml_schemas/baml_src/")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
