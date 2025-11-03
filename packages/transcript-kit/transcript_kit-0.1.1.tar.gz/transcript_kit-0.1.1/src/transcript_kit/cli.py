"""
Command-line interface for transcript-kit

Author: Kevin Callens
"""

import getpass
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from . import __version__
from .config import Config, get_config
from .processor import TranscriptProcessor
from .utils import check_yt_dlp, download_subtitle


@click.group()
@click.version_option(version=__version__, prog_name="transcript-kit")
def cli():
    """transcript-kit: AI-powered YouTube transcript processor"""
    pass


@cli.command()
@click.option(
    "--config-path",
    type=click.Path(path_type=Path),
    help="Custom config file path",
)
def setup(config_path: Optional[Path]):
    """Interactive setup wizard to configure transcript-kit"""
    click.echo("🎬 transcript-kit Setup Wizard")
    click.echo("=" * 50)
    click.echo()

    # Determine config path
    if not config_path:
        config = get_config()
        config_path = config.config_path

    # Check if config already exists
    if config_path.exists():
        if not click.confirm(f"Config file already exists at {config_path}. Overwrite?"):
            click.echo("Setup cancelled.")
            return

    click.echo("Let's set up your configuration.\n")

    # 1. API Key
    click.echo("1️⃣  OpenRouter API Key")
    click.echo("   Get yours at: https://openrouter.ai/keys")
    api_key = getpass.getpass("   Enter your API key (hidden): ").strip()

    if not api_key:
        click.echo("❌ API key is required. Setup cancelled.")
        return

    # 2. AI Model
    click.echo("\n2️⃣  AI Model Selection")
    click.echo("   Recommended: openai/gpt-oss-20b (fast, good quality)")
    click.echo("   Alternatives: openai/gpt-4o-mini, anthropic/claude-3-haiku")
    model = click.prompt("   Model", default="openai/gpt-oss-20b", type=str)

    # 3. Data Directory
    click.echo("\n3️⃣  Storage Location")
    config = get_config()  # Get default data dir
    default_data_dir = str(config.get_data_dir())
    data_dir = click.prompt("   Data directory", default=default_data_dir, type=str)

    # 4. Starter Tags
    click.echo("\n4️⃣  Tag System")
    click.echo("   Would you like to start with suggested starter tags?")
    click.echo("   (AI, Marketing, Developing, Content-Creation, Business)")
    use_starter_tags = click.confirm("   Include starter tags?", default=False)

    if use_starter_tags:
        starter_tags = ["AI", "Marketing", "Developing", "Content-Creation", "Business"]
    else:
        starter_tags = []

    # 5. Build config dictionary
    config_dict = {
        "ai": {
            "api_key": api_key,
            "model": model,
            "chunk_size": 8000,
            "context_window": 131000,
            "max_retries": 3,
            "retry_delay": 2,
        },
        "storage": {
            "data_dir": data_dir,
            "raw_subdir": "raw",
            "tags_database": "tags-database.txt",
        },
        "tags": {
            "starter_tags": starter_tags,
            "max_tags": 2,
        },
        "processing": {
            "analyze_context": True,
            "auto_tag": True,
        },
    }

    # 6. Save config
    click.echo("\n💾 Saving configuration...")

    # Create config directory
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    with open(config_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    # Set secure permissions (owner read/write only)
    import os

    os.chmod(config_path, 0o600)

    # Create data directory
    data_dir_path = Path(data_dir).expanduser()
    data_dir_path.mkdir(parents=True, exist_ok=True)
    (data_dir_path / "raw").mkdir(exist_ok=True)

    # Create tags database if starter tags were selected
    if starter_tags:
        tags_db = data_dir_path / "tags-database.txt"
        with open(tags_db, "w") as f:
            for tag in starter_tags:
                f.write(f"{tag}\n")

    click.echo(f"✅ Configuration saved to: {config_path}")
    click.echo(f"✅ Data directory created: {data_dir_path}")
    click.echo()
    click.echo("🎉 Setup complete!")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Process a video: transcript-kit process \"<youtube-url>\"")
    click.echo("  2. View config: transcript-kit config")
    click.echo("  3. Get help: transcript-kit --help")


@cli.command()
@click.argument("url")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Custom output directory (overrides config)",
)
@click.option(
    "--model",
    "-m",
    help="AI model to use (overrides config)",
)
@click.option(
    "--no-tag",
    is_flag=True,
    help="Skip automatic tagging",
)
@click.option(
    "--config-path",
    type=click.Path(path_type=Path),
    help="Custom config file path",
)
def process(url: str, output: Optional[Path], model: Optional[str], no_tag: bool, config_path: Optional[Path]):
    """Process a YouTube video transcript"""

    # Build CLI overrides
    cli_overrides = {}
    if output:
        cli_overrides["storage"] = {"data_dir": str(output)}
    if model:
        if "ai" not in cli_overrides:
            cli_overrides["ai"] = {}
        cli_overrides["ai"]["model"] = model
    if no_tag:
        if "processing" not in cli_overrides:
            cli_overrides["processing"] = {}
        cli_overrides["processing"]["auto_tag"] = False

    # Load config
    try:
        config = get_config(config_path=config_path, cli_overrides=cli_overrides)
    except Exception as e:
        click.echo(f"❌ Error loading config: {e}", err=True)
        click.echo("Run 'transcript-kit setup' to configure.", err=True)
        sys.exit(1)

    # Validate config
    is_valid, error_msg = config.validate()
    if not is_valid:
        click.echo(f"❌ Configuration error: {error_msg}", err=True)
        click.echo("Run 'transcript-kit setup' to fix configuration.", err=True)
        sys.exit(1)

    # Check yt-dlp
    yt_dlp_installed, install_msg = check_yt_dlp()
    if not yt_dlp_installed:
        click.echo(f"❌ {install_msg}", err=True)
        sys.exit(1)

    # Download subtitle
    click.echo(f"📥 Downloading subtitle from: {url}")
    raw_dir = config.get_raw_dir()
    srt_file = download_subtitle(url, raw_dir)

    if not srt_file:
        click.echo("❌ Failed to download subtitle.", err=True)
        click.echo("Possible reasons:", err=True)
        click.echo("  - Video doesn't have auto-generated subtitles", err=True)
        click.echo("  - Invalid URL", err=True)
        click.echo("  - Network error", err=True)
        sys.exit(1)

    click.echo(f"✅ Downloaded: {srt_file.name}")
    click.echo()

    # Process transcript
    try:
        processor = TranscriptProcessor(config)
        cleaned_path = processor.process_transcript(srt_file)
        click.echo()
        click.echo(f"🎉 Success! Cleaned transcript saved to:")
        click.echo(f"   {cleaned_path}")
    except Exception as e:
        click.echo(f"\n❌ Error processing transcript: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--show-secrets",
    is_flag=True,
    help="Show full API key (default: hidden)",
)
@click.option(
    "--config-path",
    type=click.Path(path_type=Path),
    help="Custom config file path",
)
def config(show_secrets: bool, config_path: Optional[Path]):
    """Show current configuration"""
    try:
        cfg = get_config(config_path=config_path)
    except Exception as e:
        click.echo(f"❌ Error loading config: {e}", err=True)
        click.echo("Run 'transcript-kit setup' to configure.", err=True)
        sys.exit(1)

    click.echo("📋 Current Configuration")
    click.echo("=" * 50)
    click.echo(f"Config file: {cfg.config_path}")
    click.echo()

    if not cfg.config_exists():
        click.echo("⚠️  No config file found.")
        click.echo("Run 'transcript-kit setup' to create one.")
        return

    click.echo(cfg.display(hide_secrets=not show_secrets))

    # Validate
    is_valid, error_msg = cfg.validate()
    if is_valid:
        click.echo("✅ Configuration is valid")
    else:
        click.echo(f"❌ Configuration error: {error_msg}", err=True)


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
