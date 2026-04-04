import time
from env import SentinelEnv
from inference import SentinelAgent
from models import Action

def run_sentinel_mission():
    print("🛡️ --- SENTINEL-DB MISSION CONTROL --- 🛡️")
    
    # 1. Initialize Environment and Agent
    env = SentinelEnv()
    agent = SentinelAgent()
    
    # 2. Reset Environment (This creates active.db from template.db)
    print("🔄 Resetting environment and loading 984-row dataset...")
    obs = env.reset()
    
    print(f"📊 Initial State: Checksum={obs.current_checksum}, Rows={obs.row_count}")
    print("-" * 50)

    # 3. The Main Mission Loop
    max_steps = 10
    for step in range(1, max_steps + 1):
        print(f"\n🧠 [STEP {step}] Agent is thinking...")
        
        try:
            # Agent looks at the observation and decides on an action
            action = agent.get_action(obs)
            print(f"📡 Action Decided: {action.action_type.upper()}")
            print(f"💻 SQL: {action.sql_command}")

            # Execute the action in the environment
            obs, reward, done, info = env.step(action)

            # Display Progress
            if obs.success:
                print(f"✅ Step Success! New Checksum: {obs.current_checksum}")
                if obs.result_set:
                    print(f"📋 Results found: {len(obs.result_set)} rows")
            else:
                print(f"❌ Step Failed: {obs.error_message}")

            # Check if mission is complete
            if done:
                print("\n🏁 Mission goal reached or step limit hit.")
                break
                
            # Small delay to keep the terminal readable
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Critical Loop Error: {e}")
            break

    print("\n" + "="*50)
    print("🏆 MISSION COMPLETE")
    print(f"Final Checksum: {obs.current_checksum}")
    print(f"Final Row Count: {obs.row_count}")
    print("="*50)

if __name__ == "__main__":
    run_sentinel_mission()