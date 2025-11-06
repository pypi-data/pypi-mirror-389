import sys, os, time, pytest, builtins
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from study_pet.pet.actions import rename_pet, feed_pet
from study_pet.data_manager import load_state, save_state, reset_state


@pytest.fixture(autouse=True)
def clean_state():
    reset_state()
    yield
    reset_state()


# rename_pet(): correct 
def test_rename_pet_interactive(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "Fluffy")
    rename_pet()
    state = load_state()
    assert state["name"] == "Fluffy"

# rename_pet(): invalid input 
def test_rename_pet_empty(monkeypatch, capsys):
    # name should be unchanged if user input is empty
    state = load_state()
    state["name"] = "Fluffy"
    save_state(state)

    monkeypatch.setattr(builtins, "input", lambda _: "")
    rename_pet()

    captured = capsys.readouterr().out
    new_state = load_state()

    
    assert "Name cannot be empty." in captured
    assert new_state["name"] == "Fluffy"

# rename_pet(): with parameter
def test_rename_pet_with_parameter(capsys):
    state = load_state()
    state["name"] = "OldName"
    save_state(state)
    
    rename_pet("NewName")
    
    new_state = load_state()
    captured = capsys.readouterr().out
    assert new_state["name"] == "NewName"
    assert "🐍 Ball python name changed to 'NewName'!" in captured 


# feed_pet(): correct case
def test_feed_pet_increases_mood(monkeypatch):
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)

    inputs = iter(["1"])  # Mouse
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    feed_pet()
    new_state = load_state()
    assert new_state["mood"] > 60

# feed_pet(): invalid case - insufficient funds
def test_feed_pet_insufficient_funds(monkeypatch, capsys):
    state = load_state()
    state["money"] = 0
    save_state(state)
    inputs = iter(["1"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    feed_pet()
    captured = capsys.readouterr().out
    assert "Not enough coins" in captured

# feed_pet(): invalid case - invalid menu item 
def test_feed_pet_invalid_choice(monkeypatch, capsys):
    state = load_state()
    state["money"] = 500
    save_state(state)

    monkeypatch.setattr(builtins, "input", lambda _: "9")
    feed_pet()

    captured = capsys.readouterr().out
    assert "Invalid choice" in captured

# feed_pet(): menu item 6 - custom food success 
def test_feed_pet_custom_food(monkeypatch):
    state = load_state()
    state["money"] = 500
    state["mood"] = 80
    save_state(state)

    inputs = iter(["6", "pancakes"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    feed_pet()
    new_state = load_state()
    assert new_state["mood"] > 80
    assert new_state["money"] < 500  

# feed_pet(): menu item 6 - custom food empty
def test_feed_pet_custom_food_empty_name(monkeypatch, capsys):
    # if user input is empty, mystery prey
    state = load_state()
    state["money"] = 500
    save_state(state)

    inputs = iter(["6", ""])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    feed_pet()
    captured = capsys.readouterr().out
    assert "mystery prey" in captured

# feed_pet(): menu item 7 - return 
def test_feed_pet_return(monkeypatch):
    # no state change should happen
    state = load_state()
    state["money"] = 500
    state["mood"] = 50
    save_state(state)

    monkeypatch.setattr(builtins, "input", lambda _: "7")
    feed_pet()
    new_state = load_state()

    assert new_state["money"] == 500
    assert new_state["mood"] == 50

# feed_pet(): with parameter - mouse (ball python food)
def test_feed_pet_with_parameter_mouse(capsys):
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)
    
    feed_pet("mouse")
    
    new_state = load_state()
    captured = capsys.readouterr().out
    assert new_state["mood"] == 68  # 60 + 8
    assert new_state["money"] == 450  # 500 - 50
    assert "mouse" in captured.lower()
    assert "🐭" in captured

# feed_pet(): with parameter - invalid food name
def test_feed_pet_invalid_food_name(capsys):
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)
    
    feed_pet("invalid_food")
    
    new_state = load_state()
    captured = capsys.readouterr().out
    assert new_state["mood"] == 60  # unchanged
    assert new_state["money"] == 500  # unchanged
    assert "Invalid food name" in captured


# feed_pet(): test all ball python foods
def test_feed_pet_rat(capsys):
    """Test feeding rat to ball python"""
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)
    
    feed_pet("rat")
    
    new_state = load_state()
    assert new_state["mood"] == 75  # 60 + 15
    assert new_state["money"] == 420  # 500 - 80
    

def test_feed_pet_cricket(capsys):
    """Test feeding cricket to ball python"""
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)
    
    feed_pet("cricket")
    
    new_state = load_state()
    assert new_state["mood"] == 65  # 60 + 5
    assert new_state["money"] == 470  # 500 - 30


def test_feed_pet_quail(capsys):
    """Test feeding quail to ball python"""
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)
    
    feed_pet("quail")
    
    new_state = load_state()
    assert new_state["mood"] == 80  # 60 + 20
    assert new_state["money"] == 370  # 500 - 130


def test_feed_pet_rabbit(capsys):
    """Test feeding rabbit to ball python"""
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)
    
    feed_pet("rabbit")
    
    new_state = load_state()
    assert new_state["mood"] == 85  # 60 + 25
    assert new_state["money"] == 350  # 500 - 150


def test_ball_python_theme_in_output(capsys):
    """Test that ball python theme appears in feed output"""
    state = load_state()
    state["money"] = 500
    state["mood"] = 60
    save_state(state)
    
    feed_pet("mouse")
    
    captured = capsys.readouterr().out
    assert "ball python" in captured.lower()