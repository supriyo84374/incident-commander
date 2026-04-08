from tasks.task1 import Task1Env
from tasks.task2 import Task2Env
from tasks.task3 import Task3Env
from models import Observation, Action

TASK_MAP = {
    "task_1": Task1Env,
    "task_2": Task2Env,
    "task_3": Task3Env
}

class IncidentCommanderEnv:
    def __init__(self, task_id: str = "task_1"):
        if task_id not in TASK_MAP:
            raise ValueError(f"Unknown task_id: {task_id}")
        self.task_id = task_id
        self._env = TASK_MAP[task_id]()

    def reset(self) -> Observation:
        return self._env.reset()

    def step(self, action: Action):
        return self._env.step(action)

    @property
    def state(self):
        # Evolved: Accesses the internal task state correctly
        return self._env.state()

    def grade(self) -> float:
        return self._env.grade()
