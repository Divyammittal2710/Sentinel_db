from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Action(BaseModel):
    """The command the AI agent sends to the environment — a single SQL statement."""
    query: str = Field(
        ...,
        description=(
            "A raw SQL statement to execute against the 'accounts' table. "
            "Examples: "
            "'UPDATE accounts SET balance = 0 WHERE balance < 0', "
            "'DELETE FROM accounts WHERE rowid NOT IN (SELECT MIN(rowid) FROM accounts GROUP BY id)', "
            "'UPDATE accounts SET status = ''ACTIVE'' WHERE status != ''ACTIVE'''"
        ),
    )


class Observation(BaseModel):
    """What the agent sees after every step — the feedback loop."""
    success: bool = Field(True, description="True if the last SQL executed without errors.")
    result_set: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Diagnostic information: counts and samples of negative balances, "
            "duplicate IDs, and invalid statuses, plus the current reward."
        ),
    )
    error_message: Optional[str] = Field(None, description="Database error message if success is False.")
    current_checksum: float = Field(0.0, description="Sum of all account balances — integrity indicator.")
    row_count: int = Field(0, description="Total number of account rows in the database.")


class State(BaseModel):
    """Internal environment state (not exposed to the agent)."""
    step_count: int = 0
    max_steps: int = 10
    is_done: bool = False
    task_id: str = "audit_easy"