---
title: Sentinel Db
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
---
=======

# Sentinel DB

A real-world database auditing environment for AI agents built on the OpenEnv framework.

## Environment Description
The agent is given a corrupted SQLite financial database and must fix negative balances,
duplicate IDs, and invalid status fields using SQL — against the clock.

## Action Space
- Type: SQL string
- Field: `query` (str) — one raw SQL statement per step

## Observation Space
- `current_checksum` (float) — sum of all balances
- `row_count` (int) — number of accounts
- `result_set` (list) — negative balance samples, duplicate ID samples, current reward
- `success` (bool) — whether last SQL executed without error
- `error_message` (str, optional) — DB error if success=False

## Tasks
| Task ID | Difficulty | Description |
|---|---|---|
| audit_easy | Easy | Static corrupted DB, no live changes |
| audit_medium | Medium | Slow chaos monkey (every 8s) drains balances and injects duplicates |
| audit_hard | Hard | Fast chaos monkey (every 2s) continuously drains balances |

## Reward
`1.0 − (negative_balances + duplicate_ids) / 50.0` — normalized to [0.0, 1.0]

## Setup
pip install -r requirements.txt
python setup_db.py
python inference.py

## Environment Variables
- `HF_TOKEN` — your API key
- `API_BASE_URL` — LLM endpoint (default: Groq)
- `MODEL_NAME` — model identifier (default: llama-3.3-70b-versatile)
- `SENTINEL_TASK` — task ID to run (default: audit_hard)
