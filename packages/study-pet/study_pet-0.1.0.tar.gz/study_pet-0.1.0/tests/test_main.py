import sys, os, pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from study_pet.__main__ import main

# start option
def test_main_start(monkeypatch):
    calls = {"started": False}
    monkeypatch.setattr(
        "study_pet.__main__.start_session", lambda: calls.update(started=True)
    )
    monkeypatch.setattr("sys.argv", ["prog", "start"])
    main()
    assert calls["started"]

# end option
def test_main_end(monkeypatch):
    calls = {"ended": False}
    monkeypatch.setattr(
        "study_pet.__main__.end_session", lambda: calls.update(ended=True)
    )
    monkeypatch.setattr("sys.argv", ["prog", "end"])
    main()
    assert calls["ended"]

# status option
def test_main_status(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["prog", "status"])
    monkeypatch.setattr("study_pet.__main__.get_status", lambda: "Pet OK")
    main()
    captured = capsys.readouterr().out
    assert "Pet OK" in captured

# feed option
def test_main_feed(monkeypatch):
    calls = {"fed": False}
    monkeypatch.setattr(
        "study_pet.__main__.feed_pet", lambda x=None: calls.update(fed=True)
    )
    monkeypatch.setattr("sys.argv", ["prog", "feed"])
    main()
    assert calls["fed"]

# feed option with parameter
def test_main_feed_with_parameter(monkeypatch):
    calls = {"fed_with": None}
    monkeypatch.setattr(
        "study_pet.__main__.feed_pet", lambda x=None: calls.update(fed_with=x)
    )
    monkeypatch.setattr("sys.argv", ["prog", "feed", "mouse"])
    main()
    assert calls["fed_with"] == "mouse"

# rename option with parameter
def test_main_rename_with_parameter(monkeypatch):
    calls = {"renamed_with": None}
    monkeypatch.setattr(
        "study_pet.__main__.rename_pet", lambda x=None: calls.update(renamed_with=x)
    )
    monkeypatch.setattr("sys.argv", ["prog", "rename", "NewPetName"])
    main()
    assert calls["renamed_with"] == "NewPetName"

# morph option
def test_main_morph(monkeypatch):
    calls = {"morph_set": False}
    monkeypatch.setattr(
        "study_pet.__main__.set_morph", lambda x=None: calls.update(morph_set=True)
    )
    monkeypatch.setattr("sys.argv", ["prog", "morph"])
    main()
    assert calls["morph_set"]

# morph option with parameter
def test_main_morph_with_parameter(monkeypatch):
    calls = {"morph_with": None}
    monkeypatch.setattr(
        "study_pet.__main__.set_morph", lambda x=None: calls.update(morph_with=x)
    )
    monkeypatch.setattr("sys.argv", ["prog", "morph", "Albino"])
    main()
    assert calls["morph_with"] == "Albino"

# unknown command
def test_main_invalid_command(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["prog", "unknown"])
    main()
    captured = capsys.readouterr().out
    assert "Unknown command" in captured

# two tries
def test_main_menu_invalid_then_exit(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["prog"])  # main menu
    inputs = iter(["invalid", "5"])  # 1) invalid menu choice, then 2) exit
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    main()
    captured = capsys.readouterr().out
    assert "Invalid option. Try again." in captured