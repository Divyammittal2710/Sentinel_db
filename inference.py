"""
Sentinel DB — Inference Script
================================
MANDATORY environment variables:
    HF_TOKEN       Your Groq / HuggingFace API key
    API_BASE_URL   LLM API endpoint  (default: Groq)
    MODEL_NAME     Model identifier  (default: llama-3.3-70b-versatile)

STDOUT FORMAT (strictly followed):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import os
import sys
import textwrap
from dotenv import load_dotenv
from openai import OpenAI
from env import SentinelEnv
from models import Action

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "llama-3.3-70b-versatile")
BENCHMARK    = "sentinel_db"
MAX_STEPS    = 10   # must finish within 20-min limit; 10 is safe


def build_prompt(obs) -> str:
    return textwrap.dedent(f"""
        You are a FinTech Database Auditor. Output ONE raw SQL statement only.
        Goal: Fix ALL of the following issues in the 'accounts' table:
          1) Negative balances  → SET balance = 0 WHERE balance < 0
          2) Duplicate IDs      → DELETE duplicate rows keeping the first rowid
          3) Invalid statuses   → SET status = 'ACTIVE' WHERE status != 'ACTIVE'
        Rules:
          - Output only SQL, no markdown, no prose.
          - Address issues in order: negatives first, then duplicates, then statuses.
        Current database state: {obs}
    """).strip()


def run_task(client: OpenAI, task_name: str) -> dict:
    """Run one full episode and return result metadata."""
    env = SentinelEnv(task_id=task_name)
    obs = env.reset(task_id=task_name)
    history_rewards = []
    final_score = 0.0
    success = False

    print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    try:
        for step in range(1, MAX_STEPS + 1):
            error_val = "null"
            action_str = "SELECT 1;"

            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": build_prompt(obs)},
                        {"role": "user",   "content": f"Current state: {obs}"},
                    ],
                    temperature=0.1,
                    max_tokens=120,
                )
                raw = completion.choices[0].message.content or "SELECT 1;"
                # Strip markdown if LLM wraps in code fences
                action_str = raw.replace("```sql", "").replace("```", "").strip()
            except Exception as llm_err:
                error_val = str(llm_err)[:120]

            obs, reward, done, info = env.step(Action(query=action_str))
            history_rewards.append(reward)

            step_error = info.get("error") or error_val
            if step_error:
                step_error = str(step_error)[:120]
            else:
                step_error = "null"

            print(
                f"[STEP] step={step} action={action_str[:80]} "
                f"reward={reward:.2f} done={str(done).lower()} error={step_error}",
                flush=True,
            )

            if done:
                break

        final_score = history_rewards[-1] if history_rewards else 0.0
        success = final_score >= 0.90

    except Exception as ep_err:
        print(f"[EPISODE ERROR] {ep_err}", flush=True, file=sys.stderr)

    rewards_str = ",".join(f"{r:.2f}" for r in history_rewards)
    print(
        f"[END] success={str(success).lower()} steps={len(history_rewards)} "
        f"score={final_score:.2f} rewards={rewards_str}",
        flush=True,
    )

    return {"task": task_name, "score": final_score, "success": success, "steps": len(history_rewards)}


def main():
    if not API_KEY:
        print("[CRITICAL] No API key found. Set HF_TOKEN or API_KEY.", flush=True, file=sys.stderr)
        sys.exit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    tasks = ["audit_easy", "audit_medium", "audit_hard"]
    results = []

    for task in tasks:
        result = run_task(client, task)
        results.append(result)

    # Summary to stderr (does not affect validator parsing)
    print("\n=== Sentinel DB — Run Summary ===", flush=True, file=sys.stderr)
    for r in results:
        print(f"  {r['task']:15s}  score={r['score']:.2f}  success={r['success']}  steps={r['steps']}", flush=True, file=sys.stderr)


if __name__ == "__main__":
    main()