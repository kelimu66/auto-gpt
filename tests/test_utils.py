import os
import pytest
from unittest.mock import patch
from autogpt.utils import (
    clean_input,
    validate_yaml_file,
    readable_file_size,
    get_bulletin_from_web,
    get_current_git_branch,
    get_latest_bulletin,
)


def test_validate_yaml_file_valid():
    with open("valid_test_file.yaml", "w") as f:
        f.write("setting: value")
    result, message = validate_yaml_file("valid_test_file.yaml")
    os.remove("valid_test_file.yaml")

    assert result == True
    assert "Successfully validated" in message


def test_validate_yaml_file_not_found():
    result, message = validate_yaml_file("non_existent_file.yaml")

    assert result == False
    assert "wasn't found" in message


def test_validate_yaml_file_invalid():
    with open("invalid_test_file.yaml", "w") as f:
        f.write("setting: value\nunindented_setting: value")
    result, message = validate_yaml_file("invalid_test_file.yaml")
    os.remove("invalid_test_file.yaml")
    print(result)
    print(message)
    assert result == False
    assert "There was an issue while trying to read" in message


def test_readable_file_size():
    size_in_bytes = 1024 * 1024 * 3.5  # 3.5 MB
    readable_size = readable_file_size(size_in_bytes)

    assert readable_size == "3.50 MB"


@patch("requests.get")
def test_get_bulletin_from_web_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "Test bulletin"
    bulletin = get_bulletin_from_web()

    assert bulletin == "Test bulletin"


@patch("requests.get")
def test_get_bulletin_from_web_failure(mock_get):
    mock_get.return_value.status_code = 404
    bulletin = get_bulletin_from_web()
    print(bulletin)
    assert bulletin == ""


def test_get_current_git_branch():
    branch_name = get_current_git_branch()

    # Assuming that the branch name will be non-empty if the function is working correctly.
    assert branch_name != ""


def test_get_latest_bulletin_no_file():
    if os.path.exists("CURRENT_BULLETIN.md"):
        os.remove("CURRENT_BULLETIN.md")

    with patch("autogpt.utils.get_bulletin_from_web", return_value=""):
        bulletin = get_latest_bulletin()
        assert bulletin == ""


def test_get_latest_bulletin_with_file():
    with open("CURRENT_BULLETIN.md", "w", encoding="utf-8") as f:
        f.write("Test bulletin")

    with patch("autogpt.utils.get_bulletin_from_web", return_value=""):
        bulletin = get_latest_bulletin()
        assert bulletin == "Test bulletin"

    os.remove("CURRENT_BULLETIN.md")


def test_get_latest_bulletin_with_new_bulletin():
    with open("CURRENT_BULLETIN.md", "w", encoding="utf-8") as f:
        f.write("Old bulletin")

    with patch("autogpt.utils.get_bulletin_from_web", return_value="New bulletin"):
        bulletin = get_latest_bulletin()
        assert "New bulletin" in bulletin

    os.remove("CURRENT_BULLETIN.md")


if __name__ == "__main__":
    pytest.main()
