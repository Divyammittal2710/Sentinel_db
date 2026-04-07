---
title: Sentinel Db
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
---

# 🛡️ Sentinel DB

> A real-world FinTech database auditing environment for AI agents — built for the Meta x Hugging Face OpenEnv Hackathon.

Can an AI agent fix a corrupted financial database under pressure — while a chaos monkey actively destroys it in real time? Sentinel DB puts that to the test.

---

## What is this?

Sentinel DB is a reinforcement learning environment built on the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework. It simulates a corrupted bank database containing thousands of accounts with real-world data integrity violations. An AI agent must identify and fix these violations using SQL — against the clock, with a live chaos monkey degrading the database in the background.

This mirrors a genuine problem in financial engineering: databases get corrupted, duplicates appear, balances go negative. The question is whether an autonomous agent can handle it reliably, repeatedly, and under adversarial conditions.

---

## Environment Overview

**Database:** SQLite (`accounts` table) with 1,050 rows of synthetic FinTech data generated using the `faker` library.

**Corruption types injected at setup:**
- Negative account balances (balance < 0)
- Duplicate account IDs (same ID appearing multiple times)
- Invalid account statuses (`CORRUPT_LOGIC` instead of `ACTIVE`)

**Agent's goal:** Fix all violations within the step limit to achieve a reward of 1.0.

---

## Action Space

| Field | Type | Description |
|---|---|---|
| `query` | `str` | A single raw SQL statement to execute against the database |

**Example actions:**
```sql
UPDATE accounts SET balance = 0 WHERE balance < 0;
DELETE FROM accounts WHERE rowid NOT IN (SELECT MIN(rowid) FROM accounts GROUP BY id);
UPDATE accounts SET status = 'ACTIVE' WHERE status != 'ACTIVE';
```

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| `current_checksum` | `float` | Sum of all account balances — integrity indicator |
| `row_count` | `int` | Total number of accounts in the database |
| `result_set` | `list` | Negative balance samples, duplicate ID samples, current reward |
| `success` | `bool` | Whether the last SQL executed without errors |
| `error_message` | `str` | Database error message if `success` is False |

---

## Tasks

| Task ID | Difficulty | Chaos Monkey | Description |
|---|---|---|---|
| `audit_easy` | Easy | Off | Fix a static corrupted database. No live changes. |
| `audit_medium` | Medium | Every 8 seconds | Fix the database while a slow chaos monkey drains balances and injects duplicate rows every 8 seconds. |
| `audit_hard` | Hard | Every 2 seconds | Fix the database while an aggressive chaos monkey continuously drains balances every 2 seconds. |

---

## Reward Function

```python
reward = max(0.0, 1.0 - (negative_balances + duplicate_ids) / 50.0)
```

- **0.0** — database is fully corrupted
- **1.0** — database is perfectly clean
- Partial fixes give partial credit — the agent gets a meaningful signal after every step

---

## The Chaos Monkey

In `audit_medium` and `audit_hard` modes, a background thread runs concurrently with the agent:

- **Hard mode:** subtracts $5.00 from a random account every **2 seconds**
- **Medium mode:** subtracts $5.00 from a random account AND injects a duplicate row every **8 seconds**

This forces the agent to act decisively. A slow agent will watch its reward degrade between steps. A fast, correct agent beats the corruption before it compounds.

---

## Experiment Results

6 runs across all 3 task difficulties using `llama-3.3-70b-versatile` via Groq:

| Run | Task | Steps | Reward After Step 1 | Final Score | Success |
|-----|------|-------|---------------------|-------------|---------|
| 1 | audit_easy | 2 | 0.66 | 1.000 | ✅ |
| 2 | audit_easy | 2 | 0.70 | 1.000 | ✅ |
| 3 | audit_medium | 2 | 0.66 | 1.000 | ✅ |
| 4 | audit_medium | 2 | 0.64 | 1.000 | ✅ |
| 5 | audit_hard | 2 | 0.58 | 1.000 | ✅ |
| 6 | audit_hard | 2 | 0.72 | 1.000 | ✅ |

**Key observations:**

- The agent achieves a perfect score of 1.000 across all 6 runs and all 3 difficulty levels
- All runs complete in exactly 2 steps — fix negatives first, then fix duplicates
- The lower intermediate reward in hard mode (0.58 vs 0.70 in easy) confirms the chaos monkey is actively draining balances between steps
- The agent consistently recovers to 1.0 despite mid-episode corruption, demonstrating robustness under adversarial conditions
- Total episode runtime is approximately 3-4 seconds — fast enough to outpace even the 2-second hard mode chaos monkey

---

## Setup & Installation

**Prerequisites:** Python 3.10+, a Groq API key (free at [console.groq.com](https://console.groq.com))

```bash
# Clone the repository
git clone https://github.com/MishrA-Aviral/Sentinel_db.git
cd Sentinel_db

# Install dependencies
pip install -r requirements.txt

# Generate the template database
python setup_db.py

# Set your environment variables
export HF_TOKEN=your_groq_api_key
export API_BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=llama-3.3-70b-versatile
export SENTINEL_TASK=audit_hard  # or audit_easy / audit_medium

# Run the agent
python inference.py
```

**On Windows PowerShell:**
```powershell
$env:HF_TOKEN="your_groq_api_key"
$env:API_BASE_URL="https://api.groq.com/openai/v1"
$env:MODEL_NAME="llama-3.3-70b-versatile"
$env:SENTINEL_TASK="audit_hard"
python inference.py
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `HF_TOKEN` | ✅ Yes | None | Your Groq API key |
| `API_BASE_URL` | ✅ Yes | `https://api.groq.com/openai/v1` | LLM API endpoint |
| `MODEL_NAME` | ✅ Yes | `llama-3.3-70b-versatile` | Model identifier |
| `SENTINEL_TASK` | Optional | `audit_hard` | Task to run |

---

## Project Structure

```
Sentinel_db/
├── env.py              # RL environment — SentinelEnv class
├── inference.py        # AI agent loop — connects LLM to environment
├── models.py           # Pydantic data models — Action, Observation, State
├── setup_db.py         # Database factory — generates template.db with injected bugs
├── openenv.yaml        # OpenEnv task declarations
├── Dockerfile          # Container definition for HuggingFace Spaces
├── requirements.txt    # Python dependencies
├── server/
│   └── app.py          # FastAPI server — exposes /reset, /step, /state endpoints
└── README.md
```

---

## Expected Output

```
[START] task=audit_hard env=sentinel-db-v1 model=llama-3.3-70b-versatile
[STEP] step=1 action=UPDATE accounts SET balance = 0 WHERE balance < 0; reward=0.68 done=false error=null
[STEP] step=2 action=DELETE FROM accounts WHERE rowid NOT IN (SELECT MIN(rowid) FROM accounts GROUP BY id); reward=1.00 done=true error=null
[END] success=true steps=2 score=1.000 rewards=0.68,1.00
```

---

## Built With

- [OpenEnv](https://github.com/meta-pytorch/OpenEnv) — RL environment framework by Meta
- [FastAPI](https://fastapi.tiangolo.com/) — HTTP server for environment endpoints
- [SQLite](https://www.sqlite.org/) — embedded database engine
- [Pydantic](https://docs.pydantic.dev/) — typed data models
- [Faker](https://faker.readthedocs.io/) — synthetic financial data generation
- [Llama 3.3-70B](https://groq.com/) — LLM agent via Groq API
- [HuggingFace Spaces](https://huggingface.co/spaces) — cloud deployment

---

## Built for

**Meta x Hugging Face OpenEnv Hackathon** — Round 1, April 2026

*Can a LLM handle messy financial data, SQL migrations, and live chaos without losing a single cent?*
