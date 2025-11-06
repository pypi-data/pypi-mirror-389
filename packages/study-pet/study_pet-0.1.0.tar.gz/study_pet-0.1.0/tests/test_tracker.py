import sys, os
import time
import pytest
import builtins

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from study_pet.tracker import (
    start_session,
    end_session,
    get_total_time,
    reset_sessions,
    manual_close,
    _auto_end_session,
)
from study_pet.data_manager import load_state, reset_state, save_state


@pytest.fixture(autouse=True)
def clean_data_file():
    reset_state()
    yield
    reset_state()


def test_start_session_creates_timestamp(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "3")
    start_session()
    state = load_state()
    assert state["last_session_start"] is not None
    assert state["session_tasks_planned"] == 3


def test_end_session_updates_total_time(monkeypatch):
    inputs = iter(["5", "3"])  # 5 tasks planned, 3 completed
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    start_session()
    time.sleep(0.5)
    end_session()
    state = load_state()
    assert state["total_study_time"] > 0
    assert state["last_session_start"] is None
    assert state["session_tasks_planned"] == 0  # reset after session ends


def test_get_total_time_matches_state():
    state = load_state()
    state["total_study_time"] = 12.34
    save_state(state)
    total_time = get_total_time()
    assert abs(total_time - 12.34) < 0.001


def test_reset_sessions_clears_active_session(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "2")
    start_session()
    reset_sessions()
    state = load_state()
    assert state["last_session_start"] is None


def test_end_session_without_start_does_not_crash():
    try:
        end_session()
        assert True
    except Exception as e:
        pytest.fail(f"end_session() raised an unexpected exception: {e}")


def test_auto_end_session_respects_manual_close(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "1")
    start_session()
    monkeypatch.setattr("study_pet.tracker.manual_close", True)
    _auto_end_session()
    state = load_state()
    # still active because manual close skipped
    assert state["last_session_start"] is not None


def test_task_rewards_coins(monkeypatch):
    """Test that completing tasks rewards coins correctly."""
    inputs = iter(["5", "3"])  # 5 tasks planned, 3 completed
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    
    state = load_state()
    initial_money = state["money"]
    
    start_session()
    time.sleep(0.1)
    end_session()
    
    state = load_state()
    # 3 tasks * 75 coins per task = 225 coins
    assert state["money"] == initial_money + 225
    assert state["session_tasks_completed"] == 3


def test_no_tasks_planned_no_rewards(monkeypatch):
    """Test that sessions with 0 tasks don't ask for completion or give rewards."""
    monkeypatch.setattr(builtins, "input", lambda _: "0")
    
    state = load_state()
    initial_money = state["money"]
    
    start_session()
    time.sleep(0.1)
    end_session()
    
    state = load_state()
    # No tasks, no rewards
    assert state["money"] == initial_money
    assert state["session_tasks_planned"] == 0


def test_completing_more_tasks_than_planned(monkeypatch):
    """Test completing more tasks than planned with confirmation."""
    inputs = iter(["3", "5", "y"])  # 3 planned, 5 completed, confirm yes
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    
    state = load_state()
    initial_money = state["money"]
    
    start_session()
    time.sleep(0.1)
    end_session()
    
    state = load_state()
    # 5 tasks * 75 coins = 375 coins
    assert state["money"] == initial_money + 375
    assert state["session_tasks_completed"] == 5


def test_start_session_validates_task_input(monkeypatch, capsys):
    """Test that start_session validates numeric input for tasks."""
    inputs = iter(["invalid", "-1", "3"])  # invalid, negative, then valid
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    
    start_session()
    
    captured = capsys.readouterr().out
    assert "Please enter a valid number" in captured or "Please enter a positive number" in captured
    
    state = load_state()
    assert state["session_tasks_planned"] == 3


def test_end_session_writes_last_session_tasks_planned(monkeypatch):
    """Ensure end_session() saves the last planned tasks to state."""
    inputs = iter(["4", "4"])  # 4 tasks planned, 4 completed
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    start_session()
    # short sleep to simulate time passing
    time.sleep(0.1)
    end_session()

    state = load_state()
    assert state.get("last_session_tasks_planned") == 4


def test_show_encouragement_during_active_session(monkeypatch, capsys):
    """Test that show_encouragement() works during an active session."""
    from study_pet.tracker import show_encouragement
    
    monkeypatch.setattr(builtins, "input", lambda _: "2")
    
    # Start a session
    start_session()
    time.sleep(0.1)
    
    # Call show_encouragement
    show_encouragement()
    
    captured = capsys.readouterr().out
    assert "You've been studying for" in captured
    assert "says:" in captured  # Encouragement message contains pet name + says
    
    # Clean up
    monkeypatch.setattr(builtins, "input", lambda _: "2")
    end_session()


def test_show_encouragement_without_active_session(capsys):
    """Test that show_encouragement() shows warning when no session is active."""
    from study_pet.tracker import show_encouragement
    
    # Ensure no active session
    state = load_state()
    state["last_session_start"] = None
    save_state(state)
    
    show_encouragement()
    
    captured = capsys.readouterr().out
    assert "No active study session" in captured
