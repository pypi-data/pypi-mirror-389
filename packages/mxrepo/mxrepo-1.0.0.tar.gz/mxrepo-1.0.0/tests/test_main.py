from argparse import Namespace
from mxrepo.main import get_branch
from mxrepo.main import hilite
from mxrepo.main import listdir
from mxrepo.main import perform_backup
from mxrepo.main import perform_branch
from mxrepo.main import perform_checkout
from mxrepo.main import perform_clone
from mxrepo.main import perform_commit
from mxrepo.main import perform_diff
from mxrepo.main import perform_pull
from mxrepo.main import perform_push
from mxrepo.main import perform_status
from mxrepo.main import query_repos
from unittest.mock import MagicMock

import json
import urllib.error


class TestListdir:
    """Tests for the listdir function."""

    def test_listdir_default_current_directory(self, tmp_path, monkeypatch):
        """Test listdir with default current directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()

        result = listdir()
        assert result == ["file1.txt", "file2.txt"]

    def test_listdir_with_path(self, tmp_path):
        """Test listdir with specific path."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()

        result = listdir(str(tmp_path))
        assert result == ["file1.txt", "file2.txt"]

    def test_listdir_returns_sorted(self, tmp_path):
        """Test that listdir returns sorted results."""
        (tmp_path / "zebra.txt").touch()
        (tmp_path / "alpha.txt").touch()
        (tmp_path / "beta.txt").touch()

        result = listdir(str(tmp_path))
        assert result == ["alpha.txt", "beta.txt", "zebra.txt"]


class TestHilite:
    """Tests for the hilite function."""

    def test_hilite_green_no_bold(self):
        """Test green color without bold."""
        result = hilite("test", "green", False)
        assert "\x1b[32m" in result
        assert "test" in result
        assert "\x1b[0m" in result
        assert "1" not in result.split("\x1b[")[1]

    def test_hilite_red_no_bold(self):
        """Test red color without bold."""
        result = hilite("test", "red", False)
        assert "\x1b[31m" in result
        assert "test" in result
        assert "\x1b[0m" in result

    def test_hilite_blue_no_bold(self):
        """Test blue color without bold."""
        result = hilite("test", "blue", False)
        assert "\x1b[34m" in result
        assert "test" in result
        assert "\x1b[0m" in result

    def test_hilite_green_with_bold(self):
        """Test green color with bold."""
        result = hilite("test", "green", True)
        assert "\x1b[32;1m" in result
        assert "test" in result
        assert "\x1b[0m" in result

    def test_hilite_unknown_color(self):
        """Test with unknown color (should not add color code)."""
        result = hilite("test", "unknown", False)
        assert "test" in result
        assert "\x1b[0m" in result


class TestGetBranch:
    """Tests for the get_branch function."""

    def test_get_branch_returns_current_branch(self, mocker):
        """Test that get_branch returns the current branch."""
        mock_process = MagicMock()
        mock_process.stdout.readlines.return_value = [
            b"  develop\n",
            b"* main\n",
            b"  feature/test\n",
        ]

        mock_popen = mocker.patch("subprocess.Popen")
        mock_popen.return_value = mock_process

        result = get_branch()
        assert result == "main"

    def test_get_branch_with_different_branch(self, mocker):
        """Test get_branch with different active branch."""
        mock_process = MagicMock()
        mock_process.stdout.readlines.return_value = [
            b"* develop\n",
            b"  main\n",
        ]

        mock_popen = mocker.patch("subprocess.Popen")
        mock_popen.return_value = mock_process

        result = get_branch()
        assert result == "develop"

    def test_get_branch_with_special_characters(self, mocker):
        """Test get_branch with branch containing special characters."""
        mock_process = MagicMock()
        mock_process.stdout.readlines.return_value = [
            b"* feature/PROJ-123-my-feature\n",
            b"  main\n",
        ]

        mock_popen = mocker.patch("subprocess.Popen")
        mock_popen.return_value = mock_process

        result = get_branch()
        assert result == "feature/PROJ-123-my-feature"


class TestQueryRepos:
    """Tests for the query_repos function."""

    def test_query_repos_organization_success(self, mocker):
        """Test querying repositories from an organization."""
        mock_response1 = MagicMock()
        mock_response1.read.return_value = json.dumps([
            {"name": "repo1"},
            {"name": "repo2"},
        ]).encode()

        mock_response2 = MagicMock()
        mock_response2.read.return_value = json.dumps([]).encode()

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_urlopen.side_effect = [mock_response1, mock_response2]

        result = query_repos("testorg")

        assert len(result) == 2
        assert result[0]["name"] == "repo1"
        assert result[1]["name"] == "repo2"

    def test_query_repos_user_fallback(self, mocker):
        """Test fallback to user endpoint when org fails."""
        mock_response1 = MagicMock()
        mock_response1.read.return_value = json.dumps([
            {"name": "user_repo1"},
        ]).encode()

        mock_response2 = MagicMock()
        mock_response2.read.return_value = json.dumps([]).encode()

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        # First call (org) fails, second call (user) succeeds, third call (pagination) returns empty
        mock_urlopen.side_effect = [
            urllib.error.URLError("Not found"),
            mock_response1,
            mock_response2,
        ]

        result = query_repos("testuser")

        assert len(result) == 1
        assert result[0]["name"] == "user_repo1"
        assert mock_urlopen.call_count == 3

    def test_query_repos_pagination(self, mocker, capsys):
        """Test that query_repos handles pagination."""
        # First page has data, second page is empty
        mock_response1 = MagicMock()
        mock_response1.read.return_value = json.dumps([
            {"name": "repo1"},
        ]).encode()

        mock_response2 = MagicMock()
        mock_response2.read.return_value = json.dumps([]).encode()

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_urlopen.side_effect = [mock_response1, mock_response2]

        result = query_repos("testorg")

        assert len(result) == 1
        # Verify pagination was attempted
        assert mock_urlopen.call_count == 2


class TestPerformClone:
    """Tests for the perform_clone function."""

    def test_perform_clone_specific_repos(self, mocker):
        """Test cloning specific repositories."""
        args = Namespace(
            context=["testorg"],
            repository=["repo1", "repo2"],
        )

        mock_call = mocker.patch("subprocess.call")

        perform_clone(args)

        assert mock_call.call_count == 2
        mock_call.assert_any_call(["git", "clone", "git@github.com:testorg/repo1.git"])
        mock_call.assert_any_call(["git", "clone", "git@github.com:testorg/repo2.git"])

    def test_perform_clone_all_repos(self, mocker):
        """Test cloning all repositories from organization."""
        args = Namespace(
            context=["testorg"],
            repository=None,
        )

        mock_query = mocker.patch("mxrepo.main.query_repos")
        mock_query.return_value = [
            {"name": "repo1"},
            {"name": "repo2"},
        ]

        mock_call = mocker.patch("subprocess.call")

        perform_clone(args)

        mock_query.assert_called_once()
        assert mock_call.call_count == 2


class TestPerformPull:
    """Tests for the perform_pull function."""

    def test_perform_pull_all_repos(self, mock_multiple_repos, mocker, monkeypatch):
        """Test pulling all repositories in directory."""
        temp_dir, repos = mock_multiple_repos
        monkeypatch.chdir(temp_dir)

        args = Namespace(repository=None)

        mock_call = mocker.patch("subprocess.call")
        mock_get_branch = mocker.patch("mxrepo.main.get_branch", return_value="main")

        perform_pull(args)

        # Should be called for each git repo (3)
        assert mock_call.call_count == 3

    def test_perform_pull_specific_repos(self, tmp_path, mocker, monkeypatch):
        """Test pulling specific repositories."""
        monkeypatch.chdir(tmp_path)

        # Create repos
        repo1 = tmp_path / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        args = Namespace(repository=["repo1"])

        mock_call = mocker.patch("subprocess.call")
        mock_get_branch = mocker.patch("mxrepo.main.get_branch", return_value="main")

        perform_pull(args)

        assert mock_call.call_count == 1
        mock_call.assert_called_with(["git", "pull", "origin", "main"])


class TestPerformStatus:
    """Tests for the perform_status function."""

    def test_perform_status_all_repos(self, mock_multiple_repos, mocker, monkeypatch):
        """Test status for all repositories."""
        temp_dir, repos = mock_multiple_repos
        monkeypatch.chdir(temp_dir)

        args = Namespace(repository=None)
        mock_call = mocker.patch("subprocess.call")

        perform_status(args)

        assert mock_call.call_count == 3

    def test_perform_status_specific_repo(self, tmp_path, mocker, monkeypatch):
        """Test status for specific repository."""
        monkeypatch.chdir(tmp_path)

        repo1 = tmp_path / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        args = Namespace(repository=["repo1"])
        mock_call = mocker.patch("subprocess.call")

        perform_status(args)

        assert mock_call.call_count == 1
        mock_call.assert_called_with(["git", "status"])


class TestPerformBranch:
    """Tests for the perform_branch function."""

    def test_perform_branch_all_repos(self, mock_multiple_repos, mocker, monkeypatch):
        """Test branch listing for all repositories."""
        temp_dir, repos = mock_multiple_repos
        monkeypatch.chdir(temp_dir)

        args = Namespace(repository=None)
        mock_call = mocker.patch("subprocess.call")

        perform_branch(args)

        assert mock_call.call_count == 3


class TestPerformDiff:
    """Tests for the perform_diff function."""

    def test_perform_diff_all_repos(self, mock_multiple_repos, mocker, monkeypatch):
        """Test diff for all repositories."""
        temp_dir, repos = mock_multiple_repos
        monkeypatch.chdir(temp_dir)

        args = Namespace(repository=None)
        mock_call = mocker.patch("subprocess.call")

        perform_diff(args)

        assert mock_call.call_count == 3


class TestPerformCommit:
    """Tests for the perform_commit function."""

    def test_perform_commit_all_repos(self, mock_multiple_repos, mocker, monkeypatch):
        """Test committing changes in all repositories."""
        temp_dir, repos = mock_multiple_repos
        monkeypatch.chdir(temp_dir)

        args = Namespace(message=["Test commit"], repository=None)
        mock_call = mocker.patch("subprocess.call")

        perform_commit(args)

        assert mock_call.call_count == 3
        for call_args in mock_call.call_args_list:
            assert call_args[0][0] == ["git", "commit", "-am", "Test commit"]

    def test_perform_commit_specific_repo(self, tmp_path, mocker, monkeypatch):
        """Test committing changes in specific repository."""
        monkeypatch.chdir(tmp_path)

        repo1 = tmp_path / "repo1"
        repo1.mkdir()
        (repo1 / ".git").mkdir()

        args = Namespace(message=["Fix bug"], repository=["repo1"])
        mock_call = mocker.patch("subprocess.call")

        perform_commit(args)

        assert mock_call.call_count == 1
        mock_call.assert_called_with(["git", "commit", "-am", "Fix bug"])


class TestPerformPush:
    """Tests for the perform_push function."""

    def test_perform_push_all_repos(self, mock_multiple_repos, mocker, monkeypatch):
        """Test pushing all repositories."""
        temp_dir, repos = mock_multiple_repos
        monkeypatch.chdir(temp_dir)

        args = Namespace(repository=None)
        mock_call = mocker.patch("subprocess.call")
        mock_get_branch = mocker.patch("mxrepo.main.get_branch", return_value="main")

        perform_push(args)

        assert mock_call.call_count == 3


class TestPerformCheckout:
    """Tests for the perform_checkout function."""

    def test_perform_checkout_all_repos(self, mock_multiple_repos, mocker, monkeypatch):
        """Test discarding changes in all repositories."""
        temp_dir, repos = mock_multiple_repos
        monkeypatch.chdir(temp_dir)

        args = Namespace(repository=None)
        mock_call = mocker.patch("subprocess.call")

        perform_checkout(args)

        assert mock_call.call_count == 3
        for call_args in mock_call.call_args_list:
            assert call_args[0][0] == ["git", "checkout", "."]


class TestPerformBackup:
    """Tests for the perform_backup function."""

    def test_perform_backup_new_repos(self, tmp_path, mocker, monkeypatch):
        """Test backing up new repositories."""
        monkeypatch.chdir(tmp_path)

        args = Namespace(context=["testorg"])

        mock_query = mocker.patch("mxrepo.main.query_repos")
        mock_query.return_value = [
            {"name": "repo1"},
            {"name": "repo2"},
        ]

        mock_perform = mocker.patch("mxrepo.main.perform")

        perform_backup(args)

        # Should create directory and clone repos
        assert (tmp_path / "testorg").exists()
        assert mock_perform.call_count == 2

    def test_perform_backup_existing_repos(self, tmp_path, mocker, monkeypatch):
        """Test backing up when repos already exist."""
        monkeypatch.chdir(tmp_path)

        # Create context directory with existing repo
        context_dir = tmp_path / "testorg"
        context_dir.mkdir()
        (context_dir / "repo1.git").mkdir()

        monkeypatch.chdir(tmp_path)

        args = Namespace(context=["testorg"])

        mock_query = mocker.patch("mxrepo.main.query_repos")
        mock_query.return_value = [
            {"name": "repo1"},
        ]

        mock_perform = mocker.patch("mxrepo.main.perform")

        perform_backup(args)

        # Should fetch instead of clone
        mock_perform.assert_called_once()
        call_args = mock_perform.call_args[0][0]
        assert "fetch" in call_args


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_non_git_directories_are_skipped(self, tmp_path, mocker, monkeypatch):
        """Test that non-git directories are skipped."""
        monkeypatch.chdir(tmp_path)

        # Create git and non-git directories
        git_repo = tmp_path / "git_repo"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        non_git = tmp_path / "non_git"
        non_git.mkdir()

        args = Namespace(repository=None)
        mock_call = mocker.patch("subprocess.call")

        perform_status(args)

        # Should only be called for git_repo
        assert mock_call.call_count == 1

    def test_files_are_skipped(self, tmp_path, mocker, monkeypatch):
        """Test that files (not directories) are skipped."""
        monkeypatch.chdir(tmp_path)

        # Create a git repo and a file
        git_repo = tmp_path / "git_repo"
        git_repo.mkdir()
        (git_repo / ".git").mkdir()

        (tmp_path / "somefile.txt").touch()

        args = Namespace(repository=None)
        mock_call = mocker.patch("subprocess.call")

        perform_status(args)

        # Should only be called for git_repo
        assert mock_call.call_count == 1
