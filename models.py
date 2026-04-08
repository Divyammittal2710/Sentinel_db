# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict, Any, Literal

# class Action(BaseModel):
#     """
#     The command the AI agent sends to the environment.
#     We use a single 'query' field for maximum LLM reliability.
#     """
#     query: str = Field(
#         ..., 
#         description="The raw SQL string to execute. Example: 'UPDATE accounts SET balance = balance - 100 WHERE id = 1'"
#     )

# class Observation(BaseModel):
#     """
#     What the agent sees after every step. 
#     This is the 'feedback' the agent uses to learn.
#     """
#     success: bool = Field(..., description="True if the SQL executed without errors.")
#     result_set: Optional[List[Dict[str, Any]]] = Field(
#         None, description="The rows returned if the action was a SELECT query."
#     )
#     error_message: Optional[str] = Field(
#         None, description="If success is False, this contains the database error."
#     )
#     current_checksum: float = Field(
#         ..., description="The total sum of all balances in the system (Integrity Check)."
#     )
#     unprocessed_chaos_events: int = Field(
#         0, description="Number of background transactions added by the Chaos Monkey."
#     )
#     row_count: int = Field(
#         0, description="Total number of accounts currently in the database."
#     )

# class State(BaseModel):
#     """
#     Internal environment state. 
#     The agent NEVER sees this, but the OpenEnv server uses it to track progress.
#     """
#     step_count: int = 0
#     max_steps: int = 20
#     is_done: bool = False
#     reward_accumulator: float = 0.0
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Action(BaseModel):
    query: str = Field(..., description="The SQL query to execute")

class Observation(BaseModel):
    success: bool = True
    result_set: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    current_checksum: float = 0.0
    row_count: int = 0