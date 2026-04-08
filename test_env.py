"""Quick environment smoke test — run locally before submitting."""
from env import SentinelEnv
from models import Action

def test_task(task_name):
    print(f"\n=== Testing task: {task_name} ===")
    env = SentinelEnv()
    obs = env.reset(task_name)
    print(f"reset OK — row_count={obs.row_count}")

    fixes = [
        "UPDATE accounts SET balance = 0 WHERE balance < 0",
        "DELETE FROM accounts WHERE rowid NOT IN (SELECT MIN(rowid) FROM accounts GROUP BY id)",
        "UPDATE accounts SET status = 'ACTIVE' WHERE status != 'ACTIVE'",
    ]
    for i, sql in enumerate(fixes, 1):
        obs, reward, done, info = env.step(Action(query=sql))
        print(f"  step {i}: reward={reward:.4f} done={done} error={info.get('error')}")
        if done:
            break
    print(f"Final reward: {reward:.4f}  ->  {'PASS' if reward >= 0.9 else 'FAIL'}")

for t in ["audit_easy", "audit_medium", "audit_hard"]:
    test_task(t)
