# from env import SentinelEnv
# from models import Action
# import sqlite3

# def run_integration_test():
#     print("🚀 Starting Sentinel-DB Integration Test...")
    
#     try:
#         env = SentinelEnv()
#         obs = env.reset()
#         print(f"✅ Environment Reset Successful.")
#         print(f"📊 Initial State: Checksum={obs.current_checksum}, Rows={obs.unprocessed_chaos_events}")
#     except Exception as e:
#         print(f"❌ Reset Failed: {e}")
#         return

#     print("\n🔍 Testing Data Validation...")
#     test_action = Action(
#         action_type="query", 
#         sql_command="SELECT * FROM accounts WHERE balance < 0;"
#     )
#     obs, reward, done, info = env.step(test_action)
    
#     if "Bob Jones" in str(obs.result_set):
#         print(f"✅ Validation Successful: Found the negative balance bug.")
#     else:
#         print(f"⚠️ Warning: Could not find expected bugs in the database.")


#     print("\n🛠️ Testing Data Correction...")
#     fix_query = "UPDATE accounts SET balance = 0 WHERE account_holder = 'Bob Jones';"
#     fix_action = Action(action_type="query", sql_command=fix_query)
    
#     obs_after, reward, done, info = env.step(fix_action)
    
#     print(f"💰 New Checksum: {obs_after.current_checksum}")
#     if obs_after.current_checksum != obs.current_checksum:
#         print(f"✅ Integrity Verified: Checksum updated after balance fix.")
#     else:
#         print(f"❌ Integrity Failed: Checksum did not change.")

#     print("\n🏁 Test Complete. If all '✅' are present, Sentinel-DB is ready for Day 4!")

# if __name__ == "__main__":
#     run_integration_test()

from env import SentinelEnv
from models import Action
import sqlite3

def run_integration_test():
    print("🚀 Starting Sentinel-DB Integration Test...")
    

    try:
        env = SentinelEnv()
        obs = env.reset()
        print(f"✅ Environment Reset Successful.")
        # Syncing with your specific model names: current_checksum and row_count
        print(f"📊 Initial State: Checksum={obs.current_checksum}, Rows={obs.row_count}")
    except Exception as e:
        print(f"❌ Reset Failed: {e}")
        return


    print("\n🔍 Testing Data Validation...")
    test_action = Action(
        action_type="query", 
        sql_command="SELECT * FROM accounts WHERE name = 'Bob Jones';"
    )
    obs, reward, done, info = env.step(test_action)
    
    if obs.result_set and "Bob Jones" in str(obs.result_set):
        print(f"✅ Validation Successful: Found Bob Jones in the database.")
    else:
        print(f"⚠️ Warning: Could not find expected data. Check if setup_db.py ran.")


    print("\n🛠️ Testing Data Correction...")

    fix_query = "UPDATE accounts SET balance = 500.0 WHERE name = 'Bob Jones';"
    fix_action = Action(
        action_type="query", 
        sql_command=fix_query
    )
    
    obs_after, reward, done, info = env.step(fix_action)
    
    print(f"💰 New Checksum: {obs_after.current_checksum}")
    if obs_after.current_checksum != obs.current_checksum:
        print(f"✅ Integrity Verified: Checksum updated after correction.")
    else:
        print(f"❌ Integrity Failed: Checksum did not change. Is your step() committing?")

    print("\n🏁 Test Complete. All systems go for the Chaos Monkey!")

if __name__ == "__main__":
    run_integration_test()