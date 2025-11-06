from . import start_session, end_session, get_status, reset_pet
from .data_manager import load_state, save_state
from .pet import rename_pet, feed_pet, set_morph, check_daily_mood_decay
from .tracker import show_encouragement
import argparse
import study_pet.tracker as tracker


def main():
    parser = argparse.ArgumentParser(description="🐍 SsstudyPet")
    parser.add_argument(
        "command",
        nargs="?",
        default="menu",
        help="Available commands: start, end, status, feed, rename, morph, encourage, menu",
    )
    parser.add_argument(
        "arg",
        nargs="?",
        default=None,
        help="Optional argument for feed (food name), rename (new name), or morph (morph type)",
    )
    args = parser.parse_args()

    check_daily_mood_decay()

    if args.command == "start":
        start_session()
    elif args.command == "end":
        end_session()
    elif args.command == "status":
        print(get_status())
    elif args.command == "feed":
        feed_pet(args.arg)
    elif args.command == "rename":
        rename_pet(args.arg)
    elif args.command == "morph":
        set_morph(args.arg)
    elif args.command == "encourage":
        show_encouragement()
    elif args.command == "menu":
        main_menu()
    else:
        print("Unknown command. Use: start | end | status | feed [food] | rename [name] | morph [type] | encourage | menu")


def actions_menu():
    """Submenu for all pet-related actions."""
    while True:
        print("\n🐍 Actions Menu:")
        print("1. Feed your ball python")
        print("2. Get encouragement")
        print("3. Back")

        choice = input("\nSelect an option (1–3): ").strip()

        if choice == "1":
            feed_pet()
        elif choice == "2":
            show_encouragement()
        elif choice == "3":
            break
        else:
            print("Invalid option. Try again.")


def settings_menu():
    """Submenu for settings and info."""
    while True:
        print("\n⚙️ Settings Menu:")
        print("1. Check ball python status")
        print("2. Rename your ball python")
        print("3. Change ball python morph")
        print("4. Reset all data")
        print("5. Back")

        choice = input("\nSelect an option (1–5): ").strip()

        if choice == "1":
            print(get_status())
        elif choice == "2":
            rename_pet()
        elif choice == "3":
            set_morph()
        elif choice == "4":
            confirm = input(
                "This will reset all progress. Type 'byebye' to confirm "
            ).lower()
            if confirm == "byebye":
                reset_pet()
        elif choice == "5":
            break
        else:
            print("Invalid option. Try again.")


def main_menu():
    """Main entry menu."""
    while True:
        print("\n� Welcome to SsstudyPet 🐍\n")
        print("1. Start studying ")
        print("2. End session")
        print("3. Actions")
        print("4. Settings")
        print("5. Close Menu (return to terminal)")
        print("6. Exit (Close SsstudyPet to terminal)")

        choice = input("\nSelect an option (1–6): ").strip()
        if choice == "1":
            start_session()
        elif choice == "2":
            end_session()
        elif choice == "3":
            actions_menu()
        elif choice == "4":
            settings_menu()
        elif choice == "5":
            tracker.manual_close = True
            break
        elif choice == "6":
            tracker.manual_close = False
            break
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()
