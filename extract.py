"""
Extract tasks, decisions, and blockers from chat messages using an LLM.
"""
import os
import json
import logging
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from openai import OpenAI, APIConnectionError, APIStatusError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from project root (same directory as this module)
load_dotenv(Path(__file__).parent / ".env")


@dataclass
class Task:
    title: str
    author: Optional[str] = None
    source_message_id: Optional[int] = None
    source_chat_id: Optional[str] = None
    source: str = "telegram"
    notes: Optional[str] = None


@dataclass
class Decision:
    topic: str
    decision: str
    rationale: Optional[str] = None
    author: Optional[str] = None
    source_message_id: Optional[int] = None
    source_chat_id: Optional[str] = None
    source: str = "telegram"


@dataclass
class Blocker:
    title: str
    reporter: Optional[str] = None
    source_message_id: Optional[int] = None
    source_chat_id: Optional[str] = None
    source: str = "telegram"


@dataclass
class ExtractionResult:
    tasks: list[Task] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)


def _get_llm_config():
    """Get LLM configuration from environment."""
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
    model = os.getenv("LLM_MODEL")
    if not model:
        logger.warning("LLM_MODEL not set in .env — LLM extraction will be skipped.")
    return base_url, model


def extract_from_messages(messages: list[dict]) -> list[ExtractionResult]:
    """Send a batch of messages to an LLM for structured extraction.

    Expects each dict to have at least 'text' and optionally
    'user_name', 'message_id', 'chat_id'.
    Returns a list with one ExtractionResult containing all findings.
    """
    if not messages:
        return []

    # Build readable text for the LLM, including metadata
    text_parts = []
    for msg in messages:
        name = msg.get("user_name", "unknown")
        text = msg.get("text", "")
        metadata = msg.get("metadata") or {}
        
        # Build message line with metadata
        line = f"[{name}]: {text}"
        
        # Add metadata annotations
        annotations = []
        if metadata.get("reactions"):
            reaction_str = ", ".join(metadata["reactions"])
            annotations.append(f"reactions=[{reaction_str}]")
        if metadata.get("reply_to_id"):
            annotations.append(f"reply_to={metadata['reply_to_id']}")
        if metadata.get("thread_id"):
            ft = "forum-topic" if metadata.get("is_forum_topic") else "thread"
            annotations.append(f"thread={metadata['thread_id']} ({ft})")
        if metadata.get("forwarded"):
            annotations.append("forwarded")
        if metadata.get("has_media"):
            annotations.append(f"media={metadata.get('media_type', 'media')}")
        if metadata.get("button_count"):
            annotations.append(f"buttons={metadata['button_count']}")
        
        if annotations:
            line += " " + " ".join(annotations)
        
        if text.strip():
            text_parts.append(line)

    if not text_parts:
        return []

    prompt = (
        "You are a project coordination assistant that extracts action items, "
        "decisions, and blockers from chat messages.\n\n"
        "Analyze the following messages and extract:\n\n"
        "**Tasks (Aufgaben):** Any action items, assignments, commitments, or "
        "things someone said they would do. Include who is responsible if "
        "mentioned.\n\n"
        "**Decisions (Entscheidungen):** Any decisions made, choices agreed upon, "
        "or conclusions reached. Include the reasoning if clear.\n\n"
        "**Blockers (Blockaden):** Any obstacles, problems, or things blocking "
        "progress. Include who reported it.\n\n"
        "Respond with ONLY a JSON object in this exact format (no explanation, "
        "no markdown):\n"
        "{\n"
        '  "tasks": [{"title": "...", "author": "name or null", "notes": "... or null"}],\n'
        '  "decisions": [{"topic": "...", "decision": "...", "rationale": "... or null", "author": "name or null"}],\n'
        '  "blockers": [{"title": "...", "reporter": "name or null"}]\n'
        "}\n\n"
        "Messages to analyze:\n"
        + "\n".join(text_parts)
    )

    try:
        base_url, model = _get_llm_config()
        # Lokale Server (LM Studio, Ollama etc.) brauchen trotzdem einen api_key
        api_key = os.getenv("OPENAI_API_KEY") or "dummy"
        client = OpenAI(base_url=base_url, api_key=api_key)

        response = client.chat.completions.create(
            model=model or "gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        raw = response.choices[0].message.content
        if not raw:
            logger.warning("LLM returned empty response.")
            return []

        # Extract JSON from possible markdown code blocks
        json_str = raw.strip()
        if json_str.startswith("```"):
            # Remove markdown code fences
            lines = json_str.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block or not line.startswith("```"):
                    json_lines.append(line)
            json_str = "\n".join(json_lines).strip()

        result_json = json.loads(json_str)

        # Map to our dataclasses
        er = ExtractionResult()
        last_msg = messages[-1] if messages else {}

        for t in result_json.get("tasks", []):
            er.tasks.append(Task(
                title=t["title"],
                author=t.get("author"),
                notes=t.get("notes"),
                source_message_id=last_msg.get("message_id"),
                source_chat_id=last_msg.get("chat_id"),
            ))

        for d in result_json.get("decisions", []):
            er.decisions.append(Decision(
                topic=d["topic"],
                decision=d["decision"],
                rationale=d.get("rationale"),
                author=d.get("author"),
                source_message_id=last_msg.get("message_id"),
                source_chat_id=last_msg.get("chat_id"),
            ))

        for b in result_json.get("blockers", []):
            er.blockers.append(Blocker(
                title=b["title"],
                reporter=b.get("reporter"),
                source_message_id=last_msg.get("message_id"),
                source_chat_id=last_msg.get("chat_id"),
            ))

        return [er]

    except (APIConnectionError, APIStatusError) as e:
        logger.error(f"LLM connection failed — is the server running? {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during LLM extraction: {e}")
        return []
