import pytest
from minecraft_textcraft import getCommand, getCommandByName, listCategories, listCommands


def test_getCommand():
    weapons = getCommand("weapons")
    assert "sword" in weapons
    assert "bow" in weapons
    assert "shield" in weapons


def test_getCommand_default():
    weapons = getCommand()
    assert "sword" in weapons


def test_getCommandByName():
    sword_art = getCommandByName("weapons", "sword")
    assert isinstance(sword_art, str)
    assert len(sword_art) > 0


def test_getCommandByName_invalid_category():
    with pytest.raises(KeyError):
        getCommandByName("invalid", "sword")


def test_getCommandByName_invalid_command():
    with pytest.raises(KeyError):
        getCommandByName("weapons", "invalid")


def test_listCategories():
    categories = listCategories()
    assert "weapons" in categories
    assert "items" in categories
    assert "tools" in categories
    assert "nature" in categories


def test_listCommands():
    all_commands = listCommands()
    assert "sword" in all_commands
    assert "heart" in all_commands


def test_listCommands_by_category():
    weapons = listCommands("weapons")
    assert "sword" in weapons
    assert "bow" in weapons
    assert "shield" in weapons
