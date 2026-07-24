"""
Extract tasks, decisions, and blockers from chat messages.
Uses regex patterns first, falls back to LLM if configured.
"""
import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# Regex patterns for German/English task detection
TASK_PATTERNS = [
    # "Machst du X?" / "Machst die API-Dokumentation?"
    re.compile(r"(?:machst\s+(?:dich\s+)?)?(\S.*(?:API|Dokumentation|Feature|Bug|Issue|Ticket|Task|Aufgabe))\??", re.IGNORECASE),
    # "Kannst du X machen?"
    re.compile(r"(?:kannst\s+(?:dich\s+)?)?(?:mache|mach)\s+(.+)", re.IGNORECASE),
    # "Ich mache X"
    re.compile(r"ich\s+(?:werde\s+)?(?:mache|mach)\s+(.+)", re.IGNORECASE),
    # "Wir machen X"
    re.compile(r"wir\s+machen\s+(.+)", re.IGNORECASE),
    # TODO markers
    re.compile(r"(?:todo|task|#task|ticket)\s*[:\-]?\s*(.+)", re.IGNORECASE),
]

# Decision patterns
DECISION_PATTERNS = [
    # "Wir nehmen X" / "Wir entscheiden uns für X"
    re.compile(r"wir\s+(?:nehmen|entscheiden\s+uns?\s+für)\s+(.+)", re.IGNORECASE),
    # "OK, X passt" / "X ist gut"
    re.compile(r"(?:passt|gut|sinnvoll)\s*(?:,\s*)?(?:für\s+)?(.+)", re.IGNORECASE),
    # "Entscheidung:" / "Decision:"
    re.compile(r"(?:entscheidung|decision)\s*[:\-]?\s*(.+)", re.IGNORECASE),
]

# Blocker patterns
BLOCKER_PATTERNS = [
    # "Blockiert durch X" / "Hänge an X"
    re.compile(r"(?:blockiert|hänge|hängst|steckst)\s+(?:durch|an|bei|in)\s+(.+)", re.IGNORECASE),
    # "Problem mit X" / "Problem: X"
    re.compile(r"problem\s+(?:mit|bei|an|in)\s+(.+)", re.IGNORECASE),
    # "Blocker:" / "Blockiert:"
    re.compile(r"(?:blocker|blockiert)\s*[:\-]?\s*(.+)", re.IGNORECASE),
]


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


def extract_from_message(text: str, user_name: Optional[str] = None,
                         message_id: Optional[int] = None,
                         chat_id: Optional[str] = None) -> ExtractionResult:
    """Extract tasks, decisions, and blockers from a single message."""
    result = ExtractionResult()
    text_clean = text.strip()

    # Skip bot messages and short non-informative messages
    if len(text_clean) < 3:
        return result

    # Check for tasks
    for pattern in TASK_PATTERNS:
        match = pattern.search(text_clean)
        if match:
            title = match.group(1).strip()
            # Clean up common noise
            title = re.sub(r'[^\w\s\-\#\.\,]+$', '', title).strip()
            if title and len(title) > 2:
                result.tasks.append(Task(
                    title=title,
                    author=user_name,
                    source_message_id=message_id,
                    source_chat_id=chat_id,
                ))

    # Check for decisions
    for pattern in DECISION_PATTERNS:
        match = pattern.search(text_clean)
        if match:
            text_after = match.group(1).strip() if match.lastindex else text_clean
            # Try to extract topic + decision
            if ":" in text_after:
                parts = text_after.split(":", 1)
                topic = parts[0].strip()
                decision = parts[1].strip()
            else:
                topic = text_after[:50]
                decision = text_after
            result.decisions.append(Decision(
                topic=topic,
                decision=decision,
                author=user_name,
                source_message_id=message_id,
                source_chat_id=chat_id,
            ))

    # Check for blockers
    for pattern in BLOCKER_PATTERNS:
        match = pattern.search(text_clean)
        if match:
            title = match.group(1).strip()
            result.blockers.append(Blocker(
                title=title,
                reporter=user_name,
                source_message_id=message_id,
                source_chat_id=chat_id,
            ))

    return result


def extract_from_messages(messages: list[dict]) -> list[ExtractionResult]:
    """Extract from a list of messages (dict with 'text', 'user_name', etc.)."""
    return [extract_from_message(
        msg.get("text", ""),
        msg.get("user_name"),
        msg.get("message_id"),
        msg.get("chat_id"),
    ) for msg in messages]


# --- LLM fallback (optional, when regex is not enough) ---

def extract_with_llm(messages: list[dict]) -> list[ExtractionResult]:
    """
    Fallback: send messages to an LLM for extraction.
    Returns structured extraction results.
    """
    # This would call your LLM endpoint
    # For now, return regex results as fallback
    return extract_from_messages(messages)
