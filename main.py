from fastapi import FastAPI, HTTPException
from env import IncidentCommanderEnv
from models import Action, StepResult, TaskResult
import yaml
import os

app = FastAPI(title="Incident Commander — SRE OpenEnv")
envs = {}

@app.get("/")
def root():
    return {"status": "Incident Commander Online", "tasks": ["task_1", "task_2", "task_3"]}

@app.get("/info")
def info():
    # Evolved: Handles pathing correctly for PowerShell/Docker environments
    base_path = os.path.dirname(__file__)
    with open(os.path.join(base_path, "openenv.yaml"), "r") as f:
        return yaml.safe_load(f)

@app.post("/reset/{task_id}")
def reset(task_id: str):
    try:
        envs[task_id] = IncidentCommanderEnv(task_id=task_id)
        return envs[task_id].reset()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step/{task_id}")
def step(task_id: str, action: Action):
    if task_id not in envs:
        raise HTTPException(status_code=400, detail="Initialize task via /reset first")
    obs, reward, done, info = envs[task_id].step(action)
    return StepResult(observation=obs, reward=reward, done=done, info=info)

@app.get("/grade/{task_id}")
def grade(task_id: str):
    if task_id not in envs:
        raise HTTPException(status_code=400, detail="Task not active")
    return TaskResult(
        task_id=task_id,
        score=envs[task_id].grade(),
        steps_taken=envs[task_id]._env.step_count,
        success=envs[task_id].grade() >= 0.5,
        reason="Automated SRE Grading"
    )
