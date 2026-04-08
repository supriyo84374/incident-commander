from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Observation(BaseModel):
    logs: List[str]
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    services_status: Dict[str, str]
    active_alerts: List[str]
    step_count: int

class Action(BaseModel):
    command: str

class Reward(BaseModel):
    value: float
    reason: str

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]

class TaskResult(BaseModel):
    task_id: str
    score: float
    steps_taken: int
    success: bool
    reason: str
