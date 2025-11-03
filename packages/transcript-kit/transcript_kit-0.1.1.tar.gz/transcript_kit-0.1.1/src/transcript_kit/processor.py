"""
Main transcript processing logic for transcript-kit

Author: Kevin Callens
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .ai_client import OpenRouterClient
from .config import Config
from .utils import format_tags_for_filename, sanitize_filename, strip_srt_formatting


class TranscriptProcessor:
    """Main processor for cleaning and tagging transcripts"""

    def __init__(self, config: Config):
        """
        Initialize processor with configuration

        Args:
            config: Configuration instance
        """
        self.config = config
        self.data_dir = config.get_data_dir()
        self.raw_dir = config.get_raw_dir()
        self.tags_db_path = config.get_tags_db_path()

        # Initialize AI client
        self.ai_client = OpenRouterClient(
            api_key=config.get("ai.api_key"),
            model=config.get("ai.model"),
            max_retries=config.get("ai.max_retries"),
            retry_delay=config.get("ai.retry_delay"),
        )

        # Load existing tags
        self.existing_tags = self._load_existing_tags()

    def _load_existing_tags(self) -> set[str]:
        """Load all tags from the database"""
        if not self.tags_db_path.exists():
            # Return starter tags from config if database doesn't exist
            starter_tags = self.config.get("tags.starter_tags", [])
            return set(starter_tags) if starter_tags else set()

        with open(self.tags_db_path, "r") as f:
            tags = set(line.strip() for line in f if line.strip())

        # Always include starter tags from config
        starter_tags = self.config.get("tags.starter_tags", [])
        if starter_tags:
            tags.update(starter_tags)

        return tags

    def _save_tag(self, tag: str) -> None:
        """
        Add a new tag to the database

        Args:
            tag: Tag to add
        """
        if tag not in self.existing_tags:
            # Ensure tags database directory exists
            self.tags_db_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.tags_db_path, "a") as f:
                f.write(f"{tag}\n")
            self.existing_tags.add(tag)

    def process_transcript(self, srt_file_path: Path, title_override: Optional[str] = None) -> Path:
        """
        Main processing pipeline

        Args:
            srt_file_path: Path to .srt file
            title_override: Optional title override (extracted from filename if not provided)

        Returns:
            Path to cleaned transcript file

        Raises:
            FileNotFoundError: If srt_file_path doesn't exist
            ValueError: If processing fails
        """
        srt_path = Path(srt_file_path)

        if not srt_path.exists():
            raise FileNotFoundError(f"File not found: {srt_file_path}")

        print(f"Processing: {srt_path.name}")

        # Read SRT file
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()

        # Step 1: Strip SRT formatting
        print("→ Stripping SRT formatting...")
        raw_text = strip_srt_formatting(srt_content)

        # Extract title from filename or use override
        if title_override:
            title = title_override
        else:
            title = srt_path.stem.replace(".en", "")

        # Step 2: Analyze context (if enabled)
        context_summary = None
        if self.config.get("processing.analyze_context", True):
            print("→ Analyzing context...")
            context_summary = self.ai_client.analyze_context(title, raw_text)
            if context_summary:
                print(f"  Context: {context_summary}")
            else:
                print("  Warning: Context analysis failed, proceeding without context")
                context_summary = "No context available"

        # Step 3: Assign tags (if enabled)
        tags = []
        if self.config.get("processing.auto_tag", True):
            print("→ Assigning tags...")
            max_tags = self.config.get("tags.max_tags", 2)
            tags = self.ai_client.assign_tags(
                title=title,
                context_summary=context_summary or "No context",
                text_sample=raw_text,
                existing_tags=list(self.existing_tags),
                max_tags=max_tags,
            )
            print(f"  Tags: {', '.join(tags)}")

            # Save any new tags
            for tag in tags:
                self._save_tag(tag)

        # Step 4: Clean text in chunks
        print("→ Cleaning transcript...")
        words = raw_text.split()

        chunk_size = self.config.get("ai.chunk_size", 8000)
        chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]

        cleaned_chunks = []
        total_chunks = len(chunks)

        print(f"  Processing in {total_chunks} chunks (~{chunk_size} words each)")

        for i, chunk in enumerate(chunks, 1):
            print(f"  Processing chunk {i}/{total_chunks}...")
            cleaned = self.ai_client.clean_chunk(chunk, context_summary or "No context", i, total_chunks)
            if cleaned:
                cleaned_chunks.append(cleaned)
            else:
                print(f"  Warning: Chunk {i} failed to clean, using original")
                cleaned_chunks.append(chunk)

        # Combine cleaned chunks
        cleaned_text = "\n\n".join(cleaned_chunks)

        # Step 5: Save cleaned transcript
        date_str = datetime.now().strftime("%Y-%m-%d")
        tags_str = format_tags_for_filename(tags)
        safe_title = sanitize_filename(title)
        cleaned_filename = f"{date_str}-{safe_title}-{tags_str}.txt"
        cleaned_path = self.data_dir / cleaned_filename

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        with open(cleaned_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Date**: {date_str}\n")
            if tags:
                f.write(f"**Tags**: {', '.join(tags)}\n")
            if context_summary:
                f.write(f"**Context**: {context_summary}\n\n")
            f.write("---\n\n")
            f.write(cleaned_text)

        print(f"✓ Saved to: {cleaned_path}")
        print(f"✓ Complete!")

        return cleaned_path
