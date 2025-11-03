"""
OpenRouter AI client for transcript-kit

Handles API communication with OpenRouter, including rate limiting
and retry logic.

SECURITY: Never logs API keys or request headers

Author: Kevin Callens
"""

import time
from typing import Optional

import requests


class OpenRouterClient:
    """Client for OpenRouter API"""

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-20b",
        max_retries: int = 3,
        retry_delay: int = 2,
    ):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key
            model: Model identifier
            max_retries: Maximum retry attempts
            retry_delay: Base delay between retries (seconds)
        """
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def call(self, prompt: str, system_message: str = "You are a helpful assistant.") -> Optional[str]:
        """
        Make API call to OpenRouter

        Args:
            prompt: User prompt
            system_message: System message for context

        Returns:
            AI response text, or None if all retries failed

        SECURITY: Never logs headers (contain API key)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/kevincallens/transcript-kit",
            "X-Title": "transcript-kit",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=data)

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                    print(f"  Rate limited. Waiting {retry_after}s before retry...")
                    time.sleep(retry_after)
                    continue

                # Raise for other HTTP errors
                response.raise_for_status()

                # Extract response
                result = response.json()
                return result["choices"][0]["message"]["content"]

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)  # Exponential backoff
                    print(f"  API error (attempt {attempt + 1}/{self.max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Log error but NEVER log headers (contain API key)
                    print(f"Error calling AI after {self.max_retries} attempts: {e}")
                    if hasattr(e, "response") and hasattr(e.response, "text"):
                        # Safe to log response text (doesn't contain API key)
                        print(f"Response: {e.response.text}")
                    return None

        return None

    def analyze_context(self, title: str, text_sample: str) -> Optional[str]:
        """
        Analyze transcript context to understand content

        Args:
            title: Video title
            text_sample: Sample of transcript text

        Returns:
            Context summary (2-3 sentences)
        """
        prompt = f"""Analyze this video transcript to understand its context.

Video Title: {title}

First 500 words of transcript:
{text_sample[:3000]}

Provide a brief 2-3 sentence summary of what this content is about and its main topics."""

        system_message = "You are an expert at analyzing content and understanding context."

        return self.call(prompt, system_message)

    def assign_tags(
        self,
        title: str,
        context_summary: str,
        text_sample: str,
        existing_tags: list[str],
        max_tags: int = 2,
    ) -> list[str]:
        """
        Assign tags to transcript

        Args:
            title: Video title
            context_summary: Context summary from analyze_context()
            text_sample: Sample of transcript text
            existing_tags: List of existing tags to prefer
            max_tags: Maximum number of tags to assign

        Returns:
            List of assigned tags (1-2 tags)
        """
        existing_tags_str = ", ".join(sorted(existing_tags)) if existing_tags else "None yet"

        prompt = f"""Assign 1-2 relevant tags to this transcript.

Video Title: {title}

Context Summary: {context_summary}

Text Sample:
{text_sample[:2000]}

EXISTING TAGS: {existing_tags_str}

CRITICAL RULES:
1. ALWAYS try to use existing tags first - reuse them whenever possible
2. Create up to {max_tags} NEW single-word tags if needed (prefer 2 separate tags over 1 compound tag)
3. Each tag should be ONE WORD only (e.g., "AI", "Design", "Marketing")
4. Only use hyphens for inseparable compound concepts (e.g., "Content-Creation", "Machine-Learning")
5. For topics like "AI Design", create TWO tags: ["AI", "Design"], NOT ["AI-Design"]
6. Use Title-Case (e.g., "AI", "Marketing", "Design", "Tutorial")

Respond with ONLY a JSON array with 1 or 2 tags, nothing else.
Example: ["AI", "Design"] or ["Marketing"] or ["Tutorial", "Python"]"""

        system_message = "You are a precise tagging system. Prefer single-word tags. Create 2 separate tags when content spans 2 distinct topics. Only output valid JSON."

        response = self.call(prompt, system_message)

        if not response:
            return ["Uncategorized"]

        # Extract JSON array from response
        import json
        import re

        try:
            match = re.search(r"\[.*?\]", response, re.DOTALL)
            if match:
                tags = json.loads(match.group())
                # Enforce maximum tags
                if len(tags) > max_tags:
                    print(f"  Warning: AI returned {len(tags)} tags, using only first {max_tags}")
                    tags = tags[:max_tags]
                return tags
            else:
                print(f"Warning: Could not parse tags from response: {response}")
                return ["Uncategorized"]
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in tags response: {response}")
            return ["Uncategorized"]

    def clean_chunk(
        self, chunk: str, context_summary: str, chunk_num: int, total_chunks: int
    ) -> Optional[str]:
        """
        Clean a chunk of transcript text

        Args:
            chunk: Chunk of transcript text
            context_summary: Context summary for context
            chunk_num: Current chunk number (1-indexed)
            total_chunks: Total number of chunks

        Returns:
            Cleaned text
        """
        prompt = f"""Clean this transcript chunk by fixing speech-to-text errors and formatting into proper paragraphs.

CONTEXT: {context_summary}

CHUNK {chunk_num}/{total_chunks}:
{chunk}

Instructions:
1. Fix obvious speech-to-text errors (homophones, missing punctuation, etc.)
2. Format into natural, readable paragraphs
3. Maintain the original meaning and tone
4. Keep all content, don't summarize
5. Use proper capitalization and punctuation

Provide ONLY the cleaned text, no explanations or metadata."""

        system_message = "You are an expert transcript editor. Clean the text while preserving all information."

        return self.call(prompt, system_message)
