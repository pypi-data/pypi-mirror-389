import sys
import subprocess
import animalsay.__main__ as main_module

# Test that the main module outputs the expected introduction and example

def test_main_module_output(capsys):
    main_module.main()
    captured = capsys.readouterr()

    assert "animalsay - A Fun Python Package" in captured.out
    assert "AVAILABLE ANIMALS:" in captured.out
    assert "AVAILABLE MOODS:" in captured.out
    assert "EXAMPLE OUTPUT:" in captured.out

    assert "animalsay.dog(" in captured.out
    assert "Hello! I'm a happy dog!" in captured.out

# Test that the main module can be run as a script

def test_main_module_runs_as_script():
    """Ensure running `python -m animalsay` works with no errors."""
    result = subprocess.run(
        [sys.executable, "-m", "animalsay"],
        capture_output=True,
        text=True
    )

    assert "=== animalsay - A Fun Python Package ===" in result.stdout
    assert "Make animals say things with moods in ASCII art!\n" in result.stdout
    assert "AVAILABLE ANIMALS" in result.stdout
    assert "AVAILABLE MOODS" in result.stdout

