"""Main entry point and public API for rogvibe."""

from __future__ import annotations

from typing import Iterable

from .apps import LotteryApp, SlotMachineApp
from .constants import FALLBACK_DEFAULTS
from .utils import detect_default_participants

# Prefer detected providers, otherwise fall back to sample names.
DEFAULT_PARTICIPANTS: list[str] = detect_default_participants() or FALLBACK_DEFAULTS

__all__ = [
    "run",
    "run_slot_machine",
    "LotteryApp",
    "SlotMachineApp",
    "DEFAULT_PARTICIPANTS",
]


def run(participants: Iterable[str] | None = None) -> None:
    """Launch the Textual app with the provided participants."""
    normalized = (
        [name.strip() for name in participants if name.strip()] if participants else []
    )
    names = normalized or list(DEFAULT_PARTICIPANTS)
    app = LotteryApp(names)
    app.run()


def run_slot_machine() -> None:
    """Launch the slot machine app."""
    app = SlotMachineApp()
    app.run()
