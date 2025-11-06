import sys, os, pytest, builtins

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from study_pet.pet.actions import set_morph
from study_pet.data_manager import load_state, save_state, reset_state


@pytest.fixture(autouse=True)
def clean_state():
    reset_state()
    yield
    reset_state()


def test_set_morph_default():
    """Test that default morph is Normal/Wild Type"""
    state = load_state()
    assert state["morph"] == "Normal/Wild Type"


def test_set_morph_with_parameter(capsys):
    """Test setting morph with parameter"""
    set_morph("Albino")
    state = load_state()
    captured = capsys.readouterr().out
    
    assert state["morph"] == "Albino"
    assert "Albino" in captured


def test_set_morph_interactive(monkeypatch, capsys):
    """Test setting morph through interactive menu"""
    monkeypatch.setattr(builtins, "input", lambda _: "5")  # Choose Mojave
    set_morph()
    state = load_state()
    captured = capsys.readouterr().out
    
    assert state["morph"] == "Mojave"
    assert "Mojave" in captured


def test_set_morph_invalid_parameter(capsys):
    """Test setting morph with invalid parameter"""
    set_morph("InvalidMorph")
    state = load_state()
    captured = capsys.readouterr().out
    
    # Should remain default
    assert state["morph"] == "Normal/Wild Type"
    assert "Invalid morph name" in captured


def test_set_morph_cancel(monkeypatch, capsys):
    """Test canceling morph selection"""
    monkeypatch.setattr(builtins, "input", lambda _: "12")  # Choose cancel option (len(morphs) + 1)
    set_morph()
    state = load_state()
    captured = capsys.readouterr().out
    
    assert state["morph"] == "Normal/Wild Type"
    assert "cancelled" in captured.lower()


def test_set_morph_case_insensitive(capsys):
    """Test that morph names are case insensitive"""
    set_morph("pAsTel")
    state = load_state()
    
    assert state["morph"] == "Pastel"


def test_all_morphs_selectable(monkeypatch):
    """Test that all 10 morphs can be selected"""
    morphs = [
        ("1", "Normal/Wild Type"),
        ("2", "Albino"),
        ("3", "Pastel"),
        ("4", "Spider"),
        ("5", "Mojave"),
        ("6", "Pinstripe"),
        ("7", "Clown"),
        ("8", "Banana"),
        ("9", "Black Pastel"),
        ("10", "Cinnamon")
    ]
    
    for choice, expected_morph in morphs:
        reset_state()
        monkeypatch.setattr(builtins, "input", lambda _, c=choice: c)
        set_morph()
        state = load_state()
        assert state["morph"] == expected_morph, f"Failed to set {expected_morph}"


def test_custom_morph_interactive(monkeypatch, capsys):
    """Test creating a custom morph through interactive menu"""
    inputs = iter(["11", "Blue Dream"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    set_morph()
    state = load_state()
    captured = capsys.readouterr().out
    
    assert state["morph"] == "Blue Dream"
    assert "custom" in captured.lower()


def test_custom_morph_empty_name(monkeypatch, capsys):
    """Test that empty custom morph name is rejected"""
    inputs = iter(["11", ""])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    set_morph()
    state = load_state()
    captured = capsys.readouterr().out
    
    assert state["morph"] == "Normal/Wild Type"  # Should remain default
    assert "cannot be empty" in captured.lower()


def test_custom_morph_with_parameter_invalid(capsys):
    """Test that invalid morph names via parameter don't update state"""
    set_morph("Super Pastel Mojave")
    state = load_state()
    captured = capsys.readouterr().out
    
    # Should remain default since it's not a preset morph
    assert state["morph"] == "Normal/Wild Type"
    assert "Invalid morph name" in captured
