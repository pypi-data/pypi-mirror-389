"""
Tracks study sessions for SsstudyPet.

Responsible for:
- Starting and ending sessions
- Updating total study time
- Triggering ball python updates (level, exp)
"""

import atexit
import signal
import time
from datetime import datetime
from .data_manager import load_state, save_state
from .pet.core import update_pet
from .pet.actions import get_encouragement


def start_session():
    """
    Begins a study session.
    If a session is already active, it will not start a new one.
    """
    state = load_state()

    if state.get("last_session_start"):
        print("A study session is already active.")
        return

    # Ask for number of tasks to complete
    while True:
        try:
            num_tasks = input("How many tasks do you plan to complete this session? ")
            num_tasks = int(num_tasks)
            if num_tasks < 0:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    state["last_session_start"] = time.time()
    state["session_tasks_planned"] = num_tasks
    state["session_tasks_completed"] = 0
    save_state(state)
    print(f"📘 Study session started at {datetime.now().strftime('%H:%M:%S')}")
    print(f"📝 Tasks planned: {num_tasks}")
    print(f"\n{get_encouragement()}")


def end_session():
    """
    Ends a study session and updates total study time.
    Also triggers a pet level/exp update and rewards coins for completed tasks.
    """
    state = load_state()
    start_time = state.get("last_session_start", None)

    if not start_time:
        print("⚠️ No active study session found.")
        return

    # Calculate elapsed time in hours
    end_time = time.time()
    elapsed_hours = (end_time - start_time) / 3600

    # Ask for completed tasks
    tasks_planned = state.get("session_tasks_planned", 0)
    if tasks_planned > 0:
        print(f"\n📝 You planned to complete {tasks_planned} task(s).")
        while True:
            try:
                tasks_completed = input("How many tasks did you complete? ")
                tasks_completed = int(tasks_completed)
                if tasks_completed < 0:
                    print("Please enter a positive number.")
                    continue
                if tasks_completed > tasks_planned:
                    confirm = input(f"You completed more than planned! Confirm {tasks_completed} tasks? (y/n) ").lower()
                    if confirm != 'y':
                        continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        # Reward coins for completed tasks
        coins_per_task = 75
        coins_earned = tasks_completed * coins_per_task
        state["money"] = state.get("money", 0) + coins_earned
        state["session_tasks_completed"] = tasks_completed
        # preserve the last planned tasks for display after session ends
        state["last_session_tasks_planned"] = tasks_planned

        print(f"✅ You completed {tasks_completed} task(s)!")
        print(f"💰 Earned {coins_earned} coins! (Total: {state['money']} coins)")
    
    # Update totals
    state["total_study_time"] += elapsed_hours
    state["last_session_start"] = None
    state["last_study_date"] = datetime.now().strftime("%Y-%m-%d")
    state["session_tasks_planned"] = 0

    save_state(state)
    print(f"\n⏱️  Study session ended. Duration: {elapsed_hours:.2f} hours")

    # Trigger pet update
    update_pet()
    print("🐍 Ball python data updated!")
    
    # Congratulate the user
    print(f"\n{get_encouragement()}")


def reset_sessions():
    """
    For testing or restarting — clears active session flag.
    """
    state = load_state()
    state["last_session_start"] = None
    save_state(state)
    print("Session reset complete.")


def get_total_time():
    """Returns the total study time stored in JSON (for tests)."""
    state = load_state()
    return state.get("total_study_time", 0.0)


def show_encouragement():
    """
    Shows an encouragement message during an active study session.
    This can be called manually or periodically to boost motivation.
    """
    state = load_state()
    if not state.get("last_session_start"):
        print("⚠️ No active study session. Start a session first!")
        return
    
    # Calculate elapsed time
    elapsed_hours = (time.time() - state.get("last_session_start", time.time())) / 3600
    elapsed_minutes = elapsed_hours * 60
    
    print(f"\n⏱️  You've been studying for {elapsed_minutes:.1f} minutes!")
    print(get_encouragement())
    print()


# Manual test
if __name__ == "__main__":
    print("Study Tracker CLI")
    print("1. start_session()")
    print("2. end_session()")
    print("3. reset_sessions()")

manual_close = False


def _auto_end_session(*args):
    state = load_state()
    if state.get("last_session_start") and not manual_close:
        print("\n Auto-saving your progress...")
        end_session()


# autosave on exit or interrupt
atexit.register(_auto_end_session)
signal.signal(signal.SIGINT, _auto_end_session)
signal.signal(signal.SIGTERM, _auto_end_session)
