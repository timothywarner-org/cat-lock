"""
Unit tests for PawGate configuration management.

WHY: Config is the foundation of the application. Bugs in config loading
or saving can cause crashes, data loss, or incorrect behavior. These tests
ensure config handles all edge cases gracefully.
"""

import json
import os
from pathlib import Path

import pytest

from src.config.config import Config, DEFAULT_HOTKEY, load


def test_default_hotkey_value():
    """
    Verify DEFAULT_HOTKEY constant has the expected value.

    WHY: The default hotkey is part of the public API contract. Other
    modules and documentation reference this value. This test ensures
    we don't accidentally change it during refactoring.

    If this test fails after an intentional change, update documentation
    and consider backwards compatibility for existing user configs.
    """
    assert DEFAULT_HOTKEY == "ctrl+l", f"Expected 'ctrl+l', got {DEFAULT_HOTKEY}"


def test_load_valid_config(
    mock_config_path,
    mock_packaged_path,
    valid_config_data
):
    """
    Test that a valid JSON config file loads correctly.

    WHY: This is the happy path - users with valid config files should
    have their settings loaded without errors. This test verifies:
    - File is read correctly
    - JSON parsing works
    - Values are returned as-is

    Args:
        mock_config_path: Fixture providing temp config file path
        mock_packaged_path: Fixture mocking bundled resources
        valid_config_data: Fixture with valid config dictionary
    """
    # WHY: Create a valid config file to test loading
    with open(mock_config_path, "w") as f:
        json.dump(valid_config_data, f)

    # WHY: load() should read and parse the JSON successfully
    loaded_config = load()

    # WHY: Verify all fields were loaded with correct values
    assert loaded_config is not None, "load() should return a dict, not None"
    assert loaded_config["hotkey"] == valid_config_data["hotkey"]
    assert loaded_config["opacity"] == valid_config_data["opacity"]
    assert loaded_config["notificationsEnabled"] == valid_config_data["notificationsEnabled"]


def test_load_missing_config_uses_defaults(
    mock_config_path,
    mock_packaged_path,
    partial_config_data
):
    """
    Test that missing config keys fall back to default values.

    WHY: Config files can have missing keys due to:
    - Upgrading from older versions (new fields added)
    - Manual editing errors
    - Corrupted writes

    The Config class should gracefully handle missing keys by using
    sensible defaults rather than crashing.

    Args:
        mock_config_path: Fixture providing temp config file path
        mock_packaged_path: Fixture mocking bundled resources
        partial_config_data: Fixture with incomplete config dict
    """
    # WHY: Create a config file with some missing keys
    with open(mock_config_path, "w") as f:
        json.dump(partial_config_data, f)

    # WHY: Config() should load without errors and use defaults
    # for missing keys
    config = Config()

    # WHY: Verify the explicitly set value was loaded
    assert config.hotkey == partial_config_data["hotkey"]

    # WHY: Verify missing values got defaults (not None, not crash)
    assert config.opacity == 0.3, "Missing opacity should default to 0.3"
    assert config.notifications_enabled is True, "Missing notificationsEnabled should default to True"


def test_config_save_persists_values(
    mock_config_path,
    mock_packaged_path,
    mock_open_about
):
    """
    Test that Config.save() correctly writes values to disk.

    WHY: save() must persist user changes for the next application run.
    This test verifies:
    - JSON is written to the correct file
    - All fields are included
    - Values match the Config object's state
    - File is valid JSON (parseable)

    Args:
        mock_config_path: Fixture providing temp config file path
        mock_packaged_path: Fixture mocking bundled resources
        mock_open_about: Fixture mocking browser opening
    """
    # WHY: Create a config with bundled defaults
    config = Config()

    # WHY: Modify the config to test persistence
    config.hotkey = "ctrl+shift+k"
    config.opacity = 0.7
    config.notifications_enabled = False

    # WHY: Save should write to disk without errors
    config.save()

    # WHY: Verify file was actually created
    assert os.path.exists(mock_config_path), f"Config file should exist at {mock_config_path}"

    # WHY: Read the file back and verify contents
    with open(mock_config_path, "r") as f:
        saved_data = json.load(f)

    # WHY: Verify all fields were saved with correct values
    assert saved_data["hotkey"] == "ctrl+shift+k", "Hotkey not saved correctly"
    assert saved_data["opacity"] == 0.7, "Opacity not saved correctly"
    assert saved_data["notificationsEnabled"] is False, "notificationsEnabled not saved correctly"


def test_config_survives_empty_file(
    mock_config_path,
    mock_packaged_path,
    mock_open_about
):
    """
    Test that Config handles an empty JSON file gracefully.

    WHY: Edge case where config file exists but is empty (0 bytes).
    This can happen due to:
    - Crash during write
    - Disk full scenario
    - User manually deleting contents

    Config should fall back to bundled defaults without crashing.

    Args:
        mock_config_path: Fixture providing temp config file path
        mock_packaged_path: Fixture mocking bundled resources
        mock_open_about: Fixture mocking browser opening
    """
    # WHY: Create an empty file to simulate corruption
    with open(mock_config_path, "w") as f:
        pass  # Empty file

    # WHY: Config() should not crash, should load bundled defaults
    config = Config()

    # WHY: Verify defaults were loaded (from bundled config.json)
    assert config.hotkey == "ctrl+l", "Should fall back to bundled default hotkey"
    assert config.opacity == 0.3, "Should fall back to bundled default opacity"
    assert config.notifications_enabled is False, "Should fall back to bundled default notifications"


def test_config_survives_invalid_json(
    mock_config_path,
    mock_packaged_path,
    mock_open_about
):
    """
    Test that Config handles malformed JSON gracefully.

    WHY: Config file can become corrupted due to:
    - Partial write from crash
    - User manual editing
    - Disk errors

    Config should detect invalid JSON and fall back to bundled defaults
    rather than crashing the application.

    Args:
        mock_config_path: Fixture providing temp config file path
        mock_packaged_path: Fixture mocking bundled resources
        mock_open_about: Fixture mocking browser opening
    """
    # WHY: Create a file with invalid JSON
    with open(mock_config_path, "w") as f:
        f.write("{this is not valid json}")

    # WHY: Config() should not crash, should load bundled defaults
    config = Config()

    # WHY: Verify defaults were loaded from bundled config
    assert config.hotkey == "ctrl+l"
    assert config.opacity == 0.3
    assert config.notifications_enabled is False


def test_config_round_trip(
    mock_config_path,
    mock_packaged_path,
    mock_open_about
):
    """
    Test that saving and loading preserves all config values.

    WHY: This is a critical integration test for config persistence.
    If values get corrupted during save/load cycle, user settings
    will be lost. This test ensures no data loss occurs.

    Args:
        mock_config_path: Fixture providing temp config file path
        mock_packaged_path: Fixture mocking bundled resources
        mock_open_about: Fixture mocking browser opening
    """
    # WHY: Create config with specific values
    config1 = Config()
    config1.hotkey = "ctrl+alt+l"
    config1.opacity = 0.8
    config1.notifications_enabled = True
    config1.save()

    # WHY: Load a fresh config from the saved file
    config2 = Config()

    # WHY: Verify all values match after round-trip
    assert config2.hotkey == "ctrl+alt+l", "Hotkey lost during round-trip"
    assert config2.opacity == 0.8, "Opacity lost during round-trip"
    assert config2.notifications_enabled is True, "Notifications setting lost during round-trip"
