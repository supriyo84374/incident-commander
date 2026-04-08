import os
import json
import httpx
from openai import OpenAI

API_BASE = os.environ.get("OPENENV_API_BASE", "http://localhost:7860")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

client = OpenAI(api_key=HF_TOKEN, base_url="[https://api-inference.huggingface.co/v1](https://api-inference.huggingface.co/v1)")
MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

def clean_json(raw_text):
    # Evolved: Removes markdown backticks if the AI provides them
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    return raw_text.strip()

def run_task(task_id: str):
    print(f"--- Starting {task_id} ---")
    obs = httpx.post(f"{API_BASE}/reset/{task_id}").json()
    done = False
    
    while not done:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": f"Return ONLY JSON: {json.dumps(obs)}"}],
            max_tokens=100
        )
        raw_content = clean_json(response.choices[0].message.content)
        try:
            action = json.loads(raw_content)
        except:
            action = {"command": "CHECK logs"} # Fallback

        res = httpx.post(f"{API_BASE}/step/{task_id}", json=action).json()
        obs, done = res["observation"], res["done"]
        print(f"Step: {obs['step_count']} | Action: {action['command']} | Reward: {res['reward']}")
    
    final = httpx.get(f"{API_BASE}/grade/{task_id}").json()
    print(f"RESULT: {final['score']}")

if __name__ == "__main__":
    for t in ["task_1", "task_2", "task_3"]:
        run_task(t)
