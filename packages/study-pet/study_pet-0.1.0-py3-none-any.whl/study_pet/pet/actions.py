"""
Pet interaction features (rename, feed, talk, etc.)
"""

from datetime import datetime, timedelta
import time
from ..data_manager import load_state, save_state
import random


def rename_pet(new_name: str = None):
    """
    Renames the ball python and saves to state.
    If no new_name is passed, will ask user input interactively.
    """
    state = load_state()
    old_name = state.get("name", "Unnamed")

    if not new_name:
        print(f"\n🐍 Current name: {old_name}")
        new_name = input("Enter new name for your ball python: ").strip()

    if not new_name:
        print("Name cannot be empty.")
        return

    state["name"] = new_name
    save_state(state)
    print(f"🐍 Ball python name changed to '{new_name}'!\n")


def feed_pet(food_name: str = None):
    """
    Feed your ball python with food purchased using money.
    Each food has different cost and mood increase.
    
    Args:
        food_name: Optional food name (mouse, rat, quail, rabbit, cricket).
                  If not provided, will show interactive menu.
    """
    state = load_state()
    name = state.get("name", "Monty")
    money = state.get("money", 0)
    mood = state.get("mood", 100)

    # Ball python appropriate foods
    foods = {
        "mouse": {"cost": 50, "mood": 8, "emoji": "🐭", "msg": "Gulp! A tasty snack!"},
        "rat": {
            "cost": 80,
            "mood": 15,
            "emoji": "🐀",
            "msg": "Mmm, satisfying meal!",
        },
        "quail": {"cost": 130, "mood": 20, "emoji": "🐦", "msg": "Exotic and delicious!"},
        "rabbit": {"cost": 150, "mood": 25, "emoji": "🐰", "msg": "What a feast!"},
        "cricket": {"cost": 30, "mood": 5, "emoji": "🦗", "msg": "A little crunchy treat!"},
        "custom": {"cost": 80, "mood": 10, "emoji": "🍽️", "msg": "Slither slither, nom nom!"},
    }
    
    # If food_name is provided, use it directly
    if food_name:
        food_name = food_name.lower().strip()
        if food_name not in foods:
            print(f"Invalid food name: {food_name}")
            print(f"Available foods: {', '.join([f for f in foods.keys() if f != 'custom'])}")
            return
        
        selected = food_name
        food = foods[selected]
        display_name = selected
        
        # check balance
        if money < food["cost"]:
            print(f"Not enough coins! {food['cost']} needed, but you have {money}.")
            return

        # apply effects
        money -= food["cost"]
        new_mood = min(100, mood + food["mood"])
        state["money"] = money
        state["mood"] = new_mood
        state["last_feed_date"] = datetime.now().strftime("%Y-%m-%d")
        save_state(state)

        print(f"\n{food['emoji']} You fed {name} the ball python a {display_name}!")
        print(food["msg"])
        print(f"🐍 Mood increased to {new_mood}/100.")
        print(f"💰 Remaining balance: {money} coins.\n")
        return
    
    # Interactive menu mode (original behavior)
    print(f"\n🐍 {name}'s current mood: {mood}/100")
    print(f"💰 Current balance: {money} coins")
    print("Choose something to feed your ball python:")
    print("1. Mouse 🐭 (Cost: 50 | +8 mood)")
    print("2. Rat 🐀 (Cost: 80 | +15 mood)")
    print("3. Quail 🐦 (Cost: 130 | +20 mood)")
    print("4. Rabbit 🐰 (Cost: 150 | +25 mood)")
    print("5. Cricket 🦗 (Cost: 30 | +5 mood)")
    print("6. Custom food ✏️ (Cost: 80 | +10 mood)")
    print("7. Return")
    choice = input("Select (1–7): ").strip()

    mapping = {
        "1": "mouse",
        "2": "rat",
        "3": "quail",
        "4": "rabbit",
        "5": "cricket",
        "6": "custom",
    }
    if choice == "7":
        return
    if choice not in mapping:
        print(" Invalid choice.")
        return

    selected = mapping[choice]
    food = foods[selected]

    # handle custom name
    if selected == "custom":
        custom_name = input("Enter your custom food name: ").strip() or "mystery prey"
        food["msg"] = f"🐍 {name} slithered over and ate your {custom_name}!"
        display_name = custom_name
    else:
        display_name = selected

    # check balance
    if money < food["cost"]:
        print(f"Not enough coins! {food['cost']} needed, but you have {money}.")
        return

    # apply effects
    money -= food["cost"]
    new_mood = min(100, mood + food["mood"])
    state["money"] = money
    state["mood"] = new_mood
    state["last_feed_date"] = datetime.now().strftime("%Y-%m-%d")
    save_state(state)

    print(f"\n{food['emoji']} You fed {name} the ball python a {display_name}!")
    print(food["msg"])
    print(f"🐍 Mood increased to {new_mood}/100.")
    print(f"💰 Remaining balance: {money} coins.\n")


def set_morph(morph_name: str = None):
    """
    Set the ball python's morph (color pattern).
    If no morph_name is passed, will show interactive menu.
    """
    state = load_state()
    current_morph = state.get("morph", "Normal/Wild Type")
    
    # Available morphs with descriptions
    morphs = {
        "1": {
            "name": "Normal/Wild Type",
            "desc": "Natural coloration with brown and tan patterns"
        },
        "2": {
            "name": "Albino",
            "desc": "Yellow, orange, and white with red/pink eyes"
        },
        "3": {
            "name": "Pastel",
            "desc": "Brightened colors with lighter yellows"
        },
        "4": {
            "name": "Spider",
            "desc": "Bold, high-contrast web-like appearance"
        },
        "5": {
            "name": "Mojave",
            "desc": "Lighter sides with prominent dorsal stripe"
        },
        "6": {
            "name": "Pinstripe",
            "desc": "Clean, thin stripe down the spine"
        },
        "7": {
            "name": "Clown",
            "desc": "Distinctive head pattern and elongated blotches"
        },
        "8": {
            "name": "Banana",
            "desc": "Bright yellow and purple/lavender coloring"
        },
        "9": {
            "name": "Black Pastel",
            "desc": "Darkened coloration with good contrast"
        },
        "10": {
            "name": "Cinnamon",
            "desc": "Rich brown and caramel tones"
        },
        "11": {
            "name": "Custom",
            "desc": "Create your own unique morph!"
        }
    }
    # If morph_name is provided directly
    if morph_name:
        morph_name = morph_name.strip()
        # Check if it matches any morph name
        found = False
        for morph_data in morphs.values():
            if morph_data["name"].lower() == morph_name.lower():
                state["morph"] = morph_data["name"]
                save_state(state)
                print(f"🐍 Your ball python's morph is now: {morph_data['name']}!")
                print(f"   {morph_data['desc']}")
                found = True
                break
        
        if not found:
            print(f"Invalid morph name: {morph_name}")
            print("Available morphs: " + ", ".join([m["name"] for m in morphs.values() if m["name"] != "Custom"]))
        return
    
    # Interactive menu mode
    print(f"\n🐍 Current morph: {current_morph}")
    print("\n✨ Choose your ball python's morph:\n")
    
    for key, morph_data in morphs.items():
        print(f"{key:>2}. {morph_data['name']:<20} - {morph_data['desc']}")
    
    print(f"\n{len(morphs) + 1}. Cancel")
    
    choice = input(f"\nSelect (1–{len(morphs) + 1}): ").strip()
    
    if choice == str(len(morphs) + 1):
        print("Morph selection cancelled.")
        return
    
    if choice not in morphs:
        print("❌ Invalid choice.")
        return
    
    # Handle custom morph option
    if choice == "11":
        custom_morph = input("\n✨ Enter your custom morph name: ").strip()
        if not custom_morph:
            print("❌ Morph name cannot be empty.")
            return
        
        state["morph"] = custom_morph
        save_state(state)
        print(f"\n🐍 Your ball python's morph is now: {custom_morph} (custom)!")
        print("✨ Your python looks unique and beautiful!\n")
        return
    
    selected_morph = morphs[choice]["name"]
    state["morph"] = selected_morph
    save_state(state)
    
    print(f"\n✨ Your ball python's morph is now: {selected_morph}!")
    print(f"   {morphs[choice]['desc']}")
    print("🐍 Your python looks beautiful!\n")

ENCOURAGEMENT_PHRASES = [
    "You're doing sssso great! Keep up the good work!",
    "Every sssstudy ssssession makes you sssmarter!",
    "Don't give up! Jussst a little more effort!",
    "I believe in you! You've got thisss!",
    "Sssslithering sssuccess is just around the corner!",
    "Sssstay focused! You're on a roll!",
    "Look at you, being sssso productive!",
    "Your dedication is insssspiring!",
    "Jussst think of all the coinsss you'll earn!",
    "Keep going! Your future ssself will thank you.",
]

def get_encouragement() -> str:
    """
    Returns a random encouraging phrase from the pet.

    The phrase is personalized with the pet's name if it has one.

    Returns:
        A string containing a formatted encouragement message.
    """
    state = load_state()
    # Get the pet's name, or use the default
    pet_name = state.get("name", "Guido") 

    # Pick a random phrase from the list
    phrase = random.choice(ENCOURAGEMENT_PHRASES)

    return f"🐍 {pet_name} says: \"{phrase}\""
