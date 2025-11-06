"""
study_pet/pet/core.py
-------------------------------------------
Core logic for SsstudyPet:
Handles leveling, experience, and status updates
based on total study time for your ball python.

Design principles:
- update_pet(): true update (writes to persistent JSON)
- get_status(): live preview (uses current session time if any, no write)
"""

from ..data_manager import load_state, save_state
from datetime import datetime
import time


def _calculate_level_exp(total_hours: float):
    """
    Convert total study hours to (level, exp).

    Level = floor(total_hours / 5) + 1
    EXP   = (total_hours % 5) * 20
    (Every 5 hours = +1 level, 100 EXP = level up)
    """
    level = int(total_hours // 5) + 1
    exp = (total_hours % 5) * 20
    return level, exp


# called when session ends
def update_pet():
    """
    Performs a *true* update of the pet’s level and experience,
    writing the results to persistent storage.
    """
    state = load_state()
    total_time = state.get("total_study_time", 0.0)
    prev_level = state.get("level", 1)

    new_level, new_exp = _calculate_level_exp(total_time)

    if new_level > prev_level:
        print(f"🐍 {state['name']} the ball python leveled up! {prev_level} → {new_level}")

    # Update state values
    state["level"] = new_level
    state["experience"] = new_exp
    state["last_study_date"] = datetime.now().strftime("%Y-%m-%d")

    save_state(state)
    return state


# shows real time data
def get_status():
    """
    Does NOT modify the JSON file.
    """
    state = load_state()
    total_time = state.get("total_study_time", 0.0)
    last_start = state.get("last_session_start", None)

    # If currently studying, include elapsed time
    if last_start is not None:
        elapsed = (time.time() - last_start) / 3600
        total_time += elapsed
    else:
        elapsed = 0.0

    # compute simulate  level/exp
    level, exp = _calculate_level_exp(total_time)

    name = state.get("name", "Unnamed")
    mood = state.get("mood", 100)
    money = state.get("money", 0)
    morph = state.get("morph", "Normal/Wild Type")

    streak = state.get("streak_days", 0)
    last_study = state.get("last_study_date", "N/A")

    studying = "Studying now" if last_start else " Idle"

    # Ball python mood descriptions
    if mood >= 80:
        mood_status = "Slithering happily!"
    elif mood >= 60:
        mood_status = "Coiled and content."
    elif mood >= 40:
        mood_status = "A bit sluggish..."
    elif mood >= 20:
        mood_status = "Needs feeding soon!"
    else:
        mood_status = "Very lethargic!"

    status = (
        f"\n🐍 Ball Python Status 🐍\n"
        f"--------------------------------\n"
        f"{name} the Ball Python\n"
        f"Morph: {morph}\n"
        f"Level: {level} ({exp:.0f} EXP)\n"
        f"Total Study Time: {total_time:.2f} hrs (+{elapsed:.2f}h current)\n"
        f"Last Study: {last_study}\n"
        f"\nMood: {mood}/100 — {mood_status}\n"
        f"Money: {money} coins\n"
        f"Streak: {streak} days\n"
        f"\nSession: {studying}\n"
        f"--------------------------------"
    )

    return status


def check_daily_mood_decay():
    """
    Called at program startup.
    Decreases pet mood based on days since last login or last feeding.
    """
    state = load_state()

    last_open_str = state.get("last_open_date")
    last_feed_str = state.get("last_feed_date")
    mood = state.get("mood", 100)

    today = datetime.now().date()
    last_open = None
    last_feed = None

    # convert stored dates
    if last_open_str:
        try:
            last_open = datetime.strptime(last_open_str, "%Y-%m-%d").date()
        except ValueError:
            last_open = today
    else:
        last_open = today

    if last_feed_str:
        try:
            last_feed = datetime.strptime(last_feed_str, "%Y-%m-%d").date()
        except ValueError:
            last_feed = today

    # calculate days passed since last open
    days_passed = (today - last_open).days
    if days_passed <= 0:
        # same day login, no decay
        state["last_open_date"] = today.strftime("%Y-%m-%d")
        save_state(state)
        return

    # base decay by days
    if days_passed == 1:
        decay = 5
    elif days_passed == 2:
        decay = 15
    elif days_passed == 3:
        decay = 35
    elif days_passed == 4:
        decay = 60
    else:
        # 5 or more days
        decay = 999  # will drop to 0 anyway

    # extra penalty if not fed yesterday
    if last_feed is None or (today - last_feed).days >= 1:
        decay += 10

    # apply decay
    new_mood = max(0, mood - decay)

    # update state
    state["mood"] = new_mood
    state["last_open_date"] = today.strftime("%Y-%m-%d")
    save_state(state)

    # feedback message
    if decay > 0:
        print(
            f"\nIt's been {days_passed} day(s) since you last visited."
            f"\nYour pet’s mood decreased by {decay} → now {new_mood}/100 💖"
        )

    if new_mood == 0:
        print("Your ball python is very lethargic... please feed it soon! 🐍")

    return new_mood


#  Manual test
if __name__ == "__main__":
    print("🔁 Checking pet status preview...")
    print(get_status())
