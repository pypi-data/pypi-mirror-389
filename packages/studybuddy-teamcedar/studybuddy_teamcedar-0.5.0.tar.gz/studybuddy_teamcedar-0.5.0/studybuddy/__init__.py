"""studybuddy — Your (unhelpfully) helpful study companion."""

from .core import (
    study_tip, motivate, excuse, study_plan, roast, break_idea,
    pomodoro_schedule, study_playlist, deadline_reminder, pep_talk, affirmation, challenge, allocate_time
)

__all__ = [
    "study_tip", "motivate", "excuse", "study_plan", "roast", "break_idea",
    "pomodoro_schedule", "study_playlist", "deadline_reminder", "pep_talk", "affirmation", "challenge", "allocate_time"
]
__version__ = "0.3.0"
