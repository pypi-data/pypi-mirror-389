import os
import sys
import json
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from study_pet import data_manager as dm


@pytest.fixture(autouse=True)
def cleanup_data_file():
    if os.path.exists(dm.DATA_PATH):
        os.remove(dm.DATA_PATH)
    yield
    if os.path.exists(dm.DATA_PATH):
        os.remove(dm.DATA_PATH)


def test_load_state_creates_default_file():
    state = dm.load_state()
    assert os.path.exists(dm.DATA_PATH)
    assert "name" in state
    assert state["level"] == 1
    assert "session_tasks_planned" in state
    assert "session_tasks_completed" in state
    assert "morph" in state
    assert state["session_tasks_planned"] == 0
    assert state["session_tasks_completed"] == 0
    assert state["morph"] == "Normal/Wild Type"


def test_save_state_writes_to_file():
    test_state = {"name": "Testy", "level": 5, "experience": 99}
    dm.save_state(test_state)
    with open(dm.DATA_PATH, "r") as f:
        data = json.load(f)
    assert data["name"] == "Testy"
    assert data["level"] == 5


def test_reset_state_resets_to_default():
    dm.save_state({"name": "WrongPet", "level": 10, "session_tasks_planned": 5, "morph": "Custom"})
    dm.reset_state()
    state = dm.load_state()
    assert state["name"] == "Guido"
    assert state["level"] == 1
    assert state["session_tasks_planned"] == 0
    assert state["session_tasks_completed"] == 0
    assert state["morph"] == "Normal/Wild Type"


def test_save_and_reload():
    s = {"name": "A", "level": 5}
    dm.save_state(s)
    re = dm.load_state()
    assert re["name"] == "A"
