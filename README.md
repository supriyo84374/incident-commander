# Incident Commander — SRE OpenEnv

## Overview
A high-fidelity Site Reliability Engineering (SRE) simulator where an AI agent
must diagnose and resolve production outages. Built for the Meta x SST PyTorch Hackathon.
Fully compliant with the OpenEnv interface specification.

## Motivation
Meta operates infrastructure at a scale where automated incident response is critical.
This environment trains and evaluates AI agents on real SRE workflows:
log analysis, root cause diagnosis, corrective action, and postmortem reporting.

## Action Space
Commands the agent can issue:
- `CHECK <resource>` — Inspect a service, log, or metric
- `RESTART <service>` — Restart a named service
- `CLEAN <path>` — Clear a directory
- `KILL <service|pid>` — Terminate a process
- `ROLLBACK <service>` — Roll back a deployment
- `POSTMORTEM <text>` — Submit incident root cause report

## Observation Space
JSON object returned after each action:
- `logs` — Last 5 system log lines
- `cpu_usage` — Float 0-100
- `memory_usage` — Float 0-100
- `disk_usage` — Float 0-100
- `services_status` — Dict of service name to up/down/degraded
- `active_alerts` — List of active alert strings
- `step_count` — Steps taken so far

## Tasks
| Task | Difficulty | Scenario |
|------|------------|----------|
| task_1 | Easy | nginx is down. Identify and restart it. |
| task_2 | Medium | Disk at 98%. Find and clean the correct directory. |
| task_3 | Hard | Memory leak in one of three workers causing cascading failure. Kill correct process + postmortem. |

## Grading (0.0 to 1.0)
Each task has a deterministic programmatic grader:
- Rewards correct diagnosis steps
- Penalizes wrong actions and excessive steps
- Task 3 caps at 0.7 without a correct postmortem

## Baseline Scores
| Task | Baseline Score |
|------|---------------|
| task_1 | 0.0 |
| task_2 | 0.0 |
| task_3 | 0.0 |

*(Run inference.py to generate real baseline scores)*

## Setup & Usage

### Local (Python)
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860
```

### Docker
```bash
docker build -t incident-commander .
docker run -p 7860:7860 incident-commander
```

### Run Baseline
```bash
export HF_TOKEN=your_token_here
export OPENENV_API_BASE=http://localhost:7860
python inference.py
```

## Hugging Face Spaces
Tag: `openenv`
Port: `7860`
