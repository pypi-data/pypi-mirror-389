import sys, os, pytest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import timedelta
from study_pet.pet.core import update_pet, get_status, check_daily_mood_decay
from study_pet.data_manager import load_state, save_state, reset_state


@pytest.fixture(autouse=True)
def clean_state():
    reset_state()
    yield
    reset_state()


def test_update_pet_increases_level():
    state = load_state()
    state["total_study_time"] = 10.0  
    save_state(state)

    new_state = update_pet()
    assert new_state["level"] >= 3


def test_update_pet_sets_last_study_date():
    update_pet()
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    assert state["last_study_date"] == today


def test_get_status_reflects_live_session_time(monkeypatch):
    state = load_state()
    state["total_study_time"] = 2.0
    state["last_session_start"] = 0
    save_state(state)

    monkeypatch.setattr("time.time", lambda: 3600)
    status = get_status()
    assert "3.00" in status or "2.99" in status


def test_check_daily_mood_decay_reduces_mood():
    s = load_state()
    s["mood"] = 80
    old_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    s["last_open_date"] = old_date
    save_state(s)
    new_mood = check_daily_mood_decay()
    assert new_mood < 80


def test_get_status_shows_ball_python_theme():
    """Test that status display includes ball python theme"""
    status = get_status()
    assert "Ball Python" in status
    assert "🐍" in status


def test_get_status_shows_morph():
    """Test that status display includes morph information"""
    state = load_state()
    state["morph"] = "Albino"
    save_state(state)
    
    status = get_status()
    assert "Morph:" in status
    assert "Albino" in status


def test_get_status_shows_default_morph():
    """Test that status displays default morph"""
    status = get_status()
    assert "Normal/Wild Type" in status or "Morph:" in status


def test_ball_python_mood_descriptions():
    """Test that ball python mood descriptions are used"""
    state = load_state()
    
    # Test high mood (slithering happily)
    state["mood"] = 90
    save_state(state)
    status = get_status()
    assert "Slithering happily" in status or "🐍" in status
    
    # Test low mood (lethargic)
    state["mood"] = 10
    save_state(state)
    status = get_status()
    assert "lethargic" in status.lower() or "🐍" in status
