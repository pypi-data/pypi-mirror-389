"""
Utility functions for transcript-kit

Author: Kevin Callens
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


def strip_srt_formatting(srt_content: str) -> str:
    """
    Remove SRT timestamps and line numbers, keeping only text

    Args:
        srt_content: Raw SRT file content

    Returns:
        Plain text with timestamps and line numbers removed
    """
    lines = srt_content.split("\n")
    text_lines = []

    for line in lines:
        line = line.strip()
        # Skip empty lines, line numbers, and timestamp lines
        if not line or line.isdigit() or "-->" in line:
            continue
        text_lines.append(line)

    return " ".join(text_lines)


def check_yt_dlp() -> tuple[bool, Optional[str]]:
    """
    Check if yt-dlp is installed and provide install instructions

    Returns:
        (is_installed, install_message)
    """
    if shutil.which("yt-dlp"):
        return True, None

    # Provide platform-specific install instructions
    import platform

    os_type = platform.system()

    install_msgs = {
        "Darwin": "Install with: brew install yt-dlp",
        "Linux": "Install with: pip install yt-dlp  or  sudo apt install yt-dlp",
        "Windows": "Install with: pip install yt-dlp",
    }

    msg = install_msgs.get(os_type, "Install with: pip install yt-dlp")
    return False, f"yt-dlp not found. {msg}"


def download_subtitle(url: str, output_dir: Path, filename_pattern: str = "%(title)s") -> Optional[Path]:
    """
    Download YouTube subtitle using yt-dlp

    Args:
        url: YouTube video URL
        output_dir: Directory to save the subtitle
        filename_pattern: yt-dlp filename pattern

    Returns:
        Path to downloaded .srt file, or None if download failed
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / f"{filename_pattern}.%(ext)s")

    cmd = [
        "yt-dlp",
        "--write-auto-subs",
        "--sub-lang",
        "en",
        "--sub-format",
        "srt",
        "--skip-download",
        "-o",
        output_template,
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Find the downloaded .srt file
        srt_files = list(output_dir.glob("*.srt"))
        if srt_files:
            # Return the most recently created file
            return max(srt_files, key=lambda p: p.stat().st_mtime)
        else:
            return None

    except subprocess.CalledProcessError as e:
        print(f"Error downloading subtitle: {e.stderr}")
        return None
    except FileNotFoundError:
        print("yt-dlp not found. Install it first.")
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Replace invalid characters with hyphens
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "-")

    # Remove multiple consecutive hyphens
    while "--" in filename:
        filename = filename.replace("--", "-")

    # Strip leading/trailing hyphens and whitespace
    filename = filename.strip("- ")

    return filename


def format_tags_for_filename(tags: list[str]) -> str:
    """
    Format tags for inclusion in filename

    Args:
        tags: List of tag strings

    Returns:
        Formatted string like "[tag1,tag2]"
    """
    if not tags:
        return "[Untagged]"
    return f"[{','.join(tags)}]"
