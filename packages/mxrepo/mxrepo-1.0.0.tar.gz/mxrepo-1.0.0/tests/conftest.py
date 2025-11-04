from unittest.mock import MagicMock

import json
import pytest


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository structure."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    return repo_dir


@pytest.fixture
def mock_multiple_repos(tmp_path):
    """Create multiple mock git repositories."""
    repos = []
    for name in ["repo1", "repo2", "repo3"]:
        repo_dir = tmp_path / name
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        repos.append(repo_dir)

    # Add a non-git directory
    non_git = tmp_path / "not_a_repo"
    non_git.mkdir()

    return tmp_path, repos


@pytest.fixture
def mock_github_api_response():
    """Create a mock GitHub API response."""
    return [
        {
            "name": "repo1",
            "clone_url": "https://github.com/testorg/repo1.git",
            "ssh_url": "git@github.com:testorg/repo1.git",
        },
        {
            "name": "repo2",
            "clone_url": "https://github.com/testorg/repo2.git",
            "ssh_url": "git@github.com:testorg/repo2.git",
        },
    ]


@pytest.fixture
def mock_git_branch_output():
    """Mock output from 'git branch' command."""
    return b"  develop\n* main\n  feature/test\n"


@pytest.fixture
def mock_subprocess_popen(mocker):
    """Mock subprocess.Popen for git commands."""
    mock_process = MagicMock()
    mock_popen = mocker.patch("subprocess.Popen")
    mock_popen.return_value = mock_process
    return mock_popen, mock_process


@pytest.fixture
def mock_subprocess_call(mocker):
    """Mock subprocess.call for git commands."""
    return mocker.patch("subprocess.call", return_value=0)


@pytest.fixture
def mock_urlopen(mocker, mock_github_api_response):
    """Mock urllib.request.urlopen for GitHub API calls."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_github_api_response).encode()
    mock_response.close.return_value = None

    mock_url = mocker.patch("urllib.request.urlopen")
    mock_url.return_value = mock_response
    return mock_url
