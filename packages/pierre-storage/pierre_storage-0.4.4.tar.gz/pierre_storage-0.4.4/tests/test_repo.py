"""Tests for Repo operations."""

from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from pierre_storage import GitStorage
from pierre_storage.errors import ApiError, RefUpdateError


class TestRepoFileOperations:
    """Tests for file operations."""

    @pytest.mark.asyncio
    async def test_get_file_stream(self, git_storage_options: dict) -> None:
        """Test getting file stream."""
        storage = GitStorage(git_storage_options)

        # Mock repo creation
        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock file stream response
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.is_success = True
        file_response.raise_for_status = MagicMock()
        file_response.aclose = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            create_client = MagicMock()
            create_client.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            create_client.__aexit__.return_value = False

            stream_client = MagicMock()
            stream_client.get = AsyncMock(return_value=file_response)
            stream_client.aclose = AsyncMock()

            mock_client_cls.side_effect = [create_client, stream_client]

            repo = await storage.create_repo(id="test-repo")
            response = await repo.get_file_stream(path="README.md", ref="main")

            assert response is not None
            assert response.status_code == 200
            await response.aclose()
            stream_client.get.assert_awaited_once()
            file_response.aclose.assert_awaited_once()
            stream_client.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_file_stream_actual_streaming(self, git_storage_options: dict) -> None:
        """Test that file streaming actually works with aiter_bytes."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock a streaming response with actual content
        file_response = MagicMock()
        file_response.status_code = 200
        file_response.is_success = True
        file_response.raise_for_status = MagicMock()
        file_response.aclose = AsyncMock()

        # Mock the async iteration over bytes
        async def mock_aiter_bytes():
            yield b"Hello, "
            yield b"world!"

        file_response.aiter_bytes = mock_aiter_bytes

        with patch("httpx.AsyncClient") as mock_client_cls:
            create_client = MagicMock()
            create_client.__aenter__.return_value.post = AsyncMock(return_value=create_response)
            create_client.__aexit__.return_value = False

            stream_client = MagicMock()
            stream_client.get = AsyncMock(return_value=file_response)
            stream_client.aclose = AsyncMock()

            mock_client_cls.side_effect = [create_client, stream_client]

            repo = await storage.create_repo(id="test-repo")
            response = await repo.get_file_stream(path="README.md", ref="main")

            # Actually consume the stream
            chunks = []
            async for chunk in response.aiter_bytes():
                chunks.append(chunk)

            content = b"".join(chunks)
            assert content == b"Hello, world!"
            assert response.status_code == 200

            await response.aclose()
            stream_client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_file_stream_ephemeral_flag(self, git_storage_options: dict) -> None:
        """Ensure ephemeral flag propagates to file requests."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        file_response = MagicMock()
        file_response.status_code = 200
        file_response.is_success = True
        file_response.raise_for_status = MagicMock()
        file_response.aclose = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            create_client = MagicMock()
            create_client.__aenter__.return_value.post = AsyncMock(return_value=create_response)
            create_client.__aexit__.return_value = False

            stream_client = MagicMock()
            stream_client.get = AsyncMock(return_value=file_response)
            stream_client.aclose = AsyncMock()

            mock_client_cls.side_effect = [create_client, stream_client]

            repo = await storage.create_repo(id="test-repo")
            response = await repo.get_file_stream(
                path="README.md",
                ref="feature/demo",
                ephemeral=True,
            )

            assert response.status_code == 200
            called_url = stream_client.get.call_args.args[0]
            parsed = urlparse(called_url)
            params = parse_qs(parsed.query)
            assert params.get("ephemeral") == ["true"]
            assert params.get("ref") == ["feature/demo"]

            await response.aclose()
            stream_client.get.assert_awaited_once()
            file_response.aclose.assert_awaited_once()
            stream_client.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_files(self, git_storage_options: dict) -> None:
        """Test listing files in repository."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        list_response = MagicMock()
        list_response.status_code = 200
        list_response.is_success = True
        list_response.json.return_value = {
            "paths": ["README.md", "src/main.py", "package.json"],
            "ref": "main",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=list_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_files(ref="main")

            assert result is not None
            assert "paths" in result
            assert len(result["paths"]) == 3
            assert "README.md" in result["paths"]

    @pytest.mark.asyncio
    async def test_list_files_ephemeral_flag(self, git_storage_options: dict) -> None:
        """Ensure ephemeral flag propagates to list files."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        list_response = MagicMock()
        list_response.status_code = 200
        list_response.is_success = True
        list_response.json.return_value = {
            "paths": ["README.md"],
            "ref": "refs/namespaces/ephemeral/refs/heads/feature/demo",
        }

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            client_instance.get = AsyncMock(return_value=list_response)

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_files(ref="feature/demo", ephemeral=True)

            assert result["paths"] == ["README.md"]
            assert result["ref"] == "refs/namespaces/ephemeral/refs/heads/feature/demo"
            called_url = client_instance.get.call_args.args[0]
            parsed = urlparse(called_url)
            params = parse_qs(parsed.query)
            assert params.get("ephemeral") == ["true"]
            assert params.get("ref") == ["feature/demo"]


class TestRepoBranchOperations:
    """Tests for branch operations."""

    @pytest.mark.asyncio
    async def test_list_branches(self, git_storage_options: dict) -> None:
        """Test listing branches."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        branches_response = MagicMock()
        branches_response.status_code = 200
        branches_response.is_success = True
        branches_response.json.return_value = {
            "branches": [
                {"cursor": "c1", "name": "main", "head_sha": "abc123", "created_at": "2025-01-01T00:00:00Z"},
                {"cursor": "c2", "name": "develop", "head_sha": "def456", "created_at": "2025-01-02T00:00:00Z"},
            ],
            "next_cursor": None,
            "has_more": False,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=branches_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_branches(limit=10)

            assert result is not None
            assert "branches" in result
            assert len(result["branches"]) == 2
            assert result["branches"][0]["name"] == "main"

    @pytest.mark.asyncio
    async def test_list_branches_with_pagination(self, git_storage_options: dict) -> None:
        """Test listing branches with pagination cursor."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        branches_response = MagicMock()
        branches_response.status_code = 200
        branches_response.is_success = True
        branches_response.json.return_value = {
            "branches": [{"cursor": "c3", "name": "feature-1", "head_sha": "ghi789", "created_at": "2025-01-03T00:00:00Z"}],
            "next_cursor": "next-page-token",
            "has_more": True,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=branches_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_branches(limit=1, cursor="some-cursor")

            assert result is not None
            assert result["next_cursor"] == "next-page-token"
            assert result["has_more"] is True

    @pytest.mark.asyncio
    async def test_create_branch(self, git_storage_options: dict) -> None:
        """Test creating a branch using the REST API."""
        storage = GitStorage(git_storage_options)

        create_repo_response = MagicMock()
        create_repo_response.status_code = 200
        create_repo_response.is_success = True
        create_repo_response.json.return_value = {"repo_id": "test-repo"}

        create_branch_response = MagicMock()
        create_branch_response.status_code = 200
        create_branch_response.is_success = True
        create_branch_response.json.return_value = {
            "message": "branch created",
            "target_branch": "feature/demo",
            "target_is_ephemeral": True,
            "commit_sha": "abc123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(
                side_effect=[create_repo_response, create_branch_response]
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.create_branch(
                base_branch="main",
                target_branch="feature/demo",
                target_is_ephemeral=True,
            )

            assert result["message"] == "branch created"
            assert result["target_branch"] == "feature/demo"
            assert result["target_is_ephemeral"] is True
            assert result["commit_sha"] == "abc123"

            # Ensure the API call was issued with the expected payload
            assert client_instance.post.await_count == 2
            branch_call = client_instance.post.await_args_list[1]
            assert branch_call.args[0].endswith("/api/v1/repos/branches/create")
            payload = branch_call.kwargs["json"]
            assert payload["base_branch"] == "main"
            assert payload["target_branch"] == "feature/demo"
            assert payload["target_is_ephemeral"] is True

    @pytest.mark.asyncio
    async def test_promote_ephemeral_branch_defaults(self, git_storage_options: dict) -> None:
        """Test promoting an ephemeral branch with default target branch."""
        storage = GitStorage(git_storage_options)

        create_repo_response = MagicMock()
        create_repo_response.status_code = 200
        create_repo_response.is_success = True
        create_repo_response.json.return_value = {"repo_id": "test-repo"}

        promote_response = MagicMock()
        promote_response.status_code = 200
        promote_response.is_success = True
        promote_response.json.return_value = {
            "message": "branch promoted",
            "target_branch": "ephemeral/demo",
            "target_is_ephemeral": False,
            "commit_sha": "def456",
        }

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(
                side_effect=[create_repo_response, promote_response]
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.promote_ephemeral_branch(baseBranch="ephemeral/demo")

            assert result["message"] == "branch promoted"
            assert result["target_branch"] == "ephemeral/demo"
            assert result["target_is_ephemeral"] is False
            assert result["commit_sha"] == "def456"

            assert client_instance.post.await_count == 2
            branch_call = client_instance.post.await_args_list[1]
            assert branch_call.args[0].endswith("/api/v1/repos/branches/create")
            payload = branch_call.kwargs["json"]
            assert payload["base_branch"] == "ephemeral/demo"
            assert payload["target_branch"] == "ephemeral/demo"
            assert payload["base_is_ephemeral"] is True
            assert payload["target_is_ephemeral"] is False

    @pytest.mark.asyncio
    async def test_promote_ephemeral_branch_custom_target(
        self,
        git_storage_options: dict,
    ) -> None:
        """Test promoting an ephemeral branch to a custom target branch."""
        storage = GitStorage(git_storage_options)

        create_repo_response = MagicMock()
        create_repo_response.status_code = 200
        create_repo_response.is_success = True
        create_repo_response.json.return_value = {"repo_id": "test-repo"}

        promote_response = MagicMock()
        promote_response.status_code = 200
        promote_response.is_success = True
        promote_response.json.return_value = {
            "message": "branch promoted",
            "target_branch": "feature/final-demo",
            "target_is_ephemeral": False,
        }

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(
                side_effect=[create_repo_response, promote_response]
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.promote_ephemeral_branch(
                base_branch="ephemeral/demo",
                target_branch="feature/final-demo",
            )

            assert result["target_branch"] == "feature/final-demo"
            assert result["target_is_ephemeral"] is False

            assert client_instance.post.await_count == 2
            branch_call = client_instance.post.await_args_list[1]
            payload = branch_call.kwargs["json"]
            assert payload["base_branch"] == "ephemeral/demo"
            assert payload["target_branch"] == "feature/final-demo"
            assert payload["base_is_ephemeral"] is True
            assert payload["target_is_ephemeral"] is False

    @pytest.mark.asyncio
    async def test_create_branch_conflict(self, git_storage_options: dict) -> None:
        """Test create_branch surfaces API errors."""
        storage = GitStorage(git_storage_options)

        create_repo_response = MagicMock()
        create_repo_response.status_code = 200
        create_repo_response.is_success = True
        create_repo_response.json.return_value = {"repo_id": "test-repo"}

        conflict_response = MagicMock()
        conflict_response.status_code = 409
        conflict_response.is_success = False
        conflict_response.json.return_value = {"message": "branch already exists"}

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(
                side_effect=[create_repo_response, conflict_response]
            )

            repo = await storage.create_repo(id="test-repo")

            with pytest.raises(ApiError) as exc_info:
                await repo.create_branch(
                    base_branch="main",
                    target_branch="feature/demo",
                )

            assert exc_info.value.status_code == 409
            assert "branch already exists" in str(exc_info.value)


class TestRepoCommitOperations:
    """Tests for commit operations."""

    @pytest.mark.asyncio
    async def test_list_commits(self, git_storage_options: dict) -> None:
        """Test listing commits."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        commits_response = MagicMock()
        commits_response.status_code = 200
        commits_response.is_success = True
        commits_response.json.return_value = {
            "commits": [
                {
                    "sha": "abc123",
                    "message": "Initial commit",
                    "author_name": "Test User",
                    "author_email": "test@example.com",
                    "committer_name": "Test User",
                    "committer_email": "test@example.com",
                    "date": "2025-01-01T00:00:00Z",
                },
                {
                    "sha": "def456",
                    "message": "Second commit",
                    "author_name": "Test User",
                    "author_email": "test@example.com",
                    "committer_name": "Test User",
                    "committer_email": "test@example.com",
                    "date": "2025-01-02T00:00:00Z",
                },
            ],
            "next_cursor": None,
            "has_more": False,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=commits_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.list_commits(branch="main", limit=10)

            assert result is not None
            assert "commits" in result
            assert len(result["commits"]) == 2
            assert result["commits"][0]["sha"] == "abc123"
            assert result["commits"][0]["message"] == "Initial commit"

    @pytest.mark.asyncio
    async def test_restore_commit(self, git_storage_options: dict) -> None:
        """Test restoring to a previous commit."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        restore_response = MagicMock()
        restore_response.status_code = 200
        restore_response.is_success = True
        restore_response.json.return_value = {
            "commit": {
                "commit_sha": "new-commit-sha",
                "tree_sha": "new-tree-sha",
                "target_branch": "main",
                "pack_bytes": 1024,
                "blob_count": 0,
            },
            "result": {
                "success": True,
                "branch": "main",
                "old_sha": "old-sha",
                "new_sha": "new-commit-sha",
                "status": "ok",
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            # Mock both create and restore
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[create_response, restore_response]
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.restore_commit(
                target_branch="main",
                target_commit_sha="abc123",
                commit_message="Restore commit",
                author={"name": "Test", "email": "test@example.com"},
            )

            assert result is not None
            assert result["commit_sha"] == "new-commit-sha"
            assert result["ref_update"]["branch"] == "main"
            assert result["ref_update"]["new_sha"] == "new-commit-sha"
            assert result["ref_update"]["old_sha"] == "old-sha"


class TestRepoDiffOperations:
    """Tests for diff operations."""

    @pytest.mark.asyncio
    async def test_get_branch_diff(self, git_storage_options: dict) -> None:
        """Test getting branch diff."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        diff_response = MagicMock()
        diff_response.status_code = 200
        diff_response.is_success = True
        diff_response.json.return_value = {
            "branch": "feature",
            "base": "main",
            "stats": {"additions": 10, "deletions": 5, "files_changed": 2},
            "files": [
                {
                    "path": "README.md",
                    "state": "modified",
                    "raw": "diff --git ...",
                    "bytes": 100,
                    "is_eof": True,
                },
                {
                    "path": "new-file.py",
                    "state": "added",
                    "raw": "diff --git ...",
                    "bytes": 200,
                    "is_eof": True,
                },
            ],
            "filtered_files": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=diff_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.get_branch_diff(branch="feature", base="main")

            assert result is not None
            assert "stats" in result
            assert result["stats"]["additions"] == 10
            assert len(result["files"]) == 2

    @pytest.mark.asyncio
    async def test_get_commit_diff(self, git_storage_options: dict) -> None:
        """Test getting commit diff."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        diff_response = MagicMock()
        diff_response.status_code = 200
        diff_response.is_success = True
        diff_response.json.return_value = {
            "sha": "abc123",
            "stats": {"additions": 3, "deletions": 1, "files_changed": 1},
            "files": [
                {
                    "path": "config.json",
                    "state": "modified",
                    "raw": "diff --git a/config.json b/config.json...",
                    "bytes": 150,
                    "is_eof": True,
                }
            ],
            "filtered_files": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=create_response
            )
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=diff_response
            )

            repo = await storage.create_repo(id="test-repo")
            result = await repo.get_commit_diff(sha="abc123")

            assert result is not None
            assert "stats" in result
            assert result["stats"]["files_changed"] == 1
            assert result["files"][0]["path"] == "config.json"


class TestRepoUpstreamOperations:
    """Tests for upstream operations."""

    @pytest.mark.asyncio
    async def test_pull_upstream(self, git_storage_options: dict) -> None:
        """Test pulling from upstream."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        pull_response = MagicMock()
        pull_response.status_code = 202
        pull_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(side_effect=[create_response, pull_response])

            repo = await storage.create_repo(id="test-repo")
            # Should not raise an exception
            await repo.pull_upstream(ref="main")

    @pytest.mark.asyncio
    async def test_restore_commit_json_decode_error(self, git_storage_options: dict) -> None:
        """Test restoring commit with non-JSON response (e.g., CDN HTML on 5xx)."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        # Mock a 502 response with HTML instead of JSON
        restore_response = MagicMock()
        restore_response.status_code = 502
        restore_response.is_success = False
        restore_response.reason_phrase = "Bad Gateway"
        # Simulate JSON decode error
        restore_response.json.side_effect = Exception("JSON decode error")
        restore_response.aread = AsyncMock(return_value=b"<html><body>502 Bad Gateway</body></html>")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[create_response, restore_response]
            )

            repo = await storage.create_repo(id="test-repo")

            with pytest.raises(RefUpdateError) as exc_info:
                await repo.restore_commit(
                    target_branch="main",
                    target_commit_sha="abc123",
                    commit_message="Restore commit",
                    author={"name": "Test", "email": "test@example.com"},
                )

            # Verify we got a RefUpdateError with meaningful message
            assert "502" in str(exc_info.value)
            assert "Bad Gateway" in str(exc_info.value)
            assert exc_info.value.status == "unavailable"  # 502 maps to "unavailable"

    @pytest.mark.asyncio
    async def test_pull_upstream_no_branch(self, git_storage_options: dict) -> None:
        """Test pulling from upstream without specifying branch."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        pull_response = MagicMock()
        pull_response.status_code = 202
        pull_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(side_effect=[create_response, pull_response])

            repo = await storage.create_repo(id="test-repo")
            # Should work without branch option
            await repo.pull_upstream()

    @pytest.mark.asyncio
    async def test_create_commit_from_diff(self, git_storage_options: dict) -> None:
        """Test creating a commit directly from a diff."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(
            return_value=(
                b'{"commit":{"commit_sha":"diff123","tree_sha":"tree123","target_branch":"main",'
                b'"pack_bytes":512,"blob_count":0},"result":{"success":true,"status":"ok",'
                b'"branch":"main","old_sha":"old123","new_sha":"diff123"}}'
            )
        )

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo(id="test-repo")
            result = await repo.create_commit_from_diff(
                target_branch="main",
                commit_message="Apply diff",
                diff="--- a/file.txt\n+++ b/file.txt\n@@\n+hello world\n",
                author={"name": "Test", "email": "test@example.com"},
            )

            assert result["commit_sha"] == "diff123"
            assert result["ref_update"]["new_sha"] == "diff123"

            client_instance.stream.assert_called_once()
            args, _ = client_instance.stream.call_args
            assert args[0] == "POST"
            assert args[1].endswith("/api/v1/repos/diff-commit")

    @pytest.mark.asyncio
    async def test_create_commit_from_diff_failure(self, git_storage_options: dict) -> None:
        """Test diff commit raising RefUpdateError on failure."""
        storage = GitStorage(git_storage_options)

        create_response = MagicMock()
        create_response.status_code = 200
        create_response.is_success = True
        create_response.json.return_value = {"repo_id": "test-repo"}

        stream_response = MagicMock()
        stream_response.is_success = True
        stream_response.aread = AsyncMock(
            return_value=(
                b'{"commit":{"commit_sha":"fail123","tree_sha":"tree123","target_branch":"main",'
                b'"pack_bytes":512,"blob_count":0},"result":{"success":false,"status":"rejected",'
                b'"message":"conflict detected","branch":"main","old_sha":"old123","new_sha":"fail123"}}'
            )
        )

        with patch("httpx.AsyncClient") as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            client_instance.post = AsyncMock(return_value=create_response)
            stream_context = MagicMock()
            stream_context.__aenter__ = AsyncMock(return_value=stream_response)
            stream_context.__aexit__ = AsyncMock(return_value=None)
            client_instance.stream = MagicMock(return_value=stream_context)

            repo = await storage.create_repo(id="test-repo")

            with pytest.raises(RefUpdateError) as exc_info:
                await repo.create_commit_from_diff(
                    target_branch="main",
                    commit_message="Apply diff",
                    diff="@diff-content",
                    author={"name": "Test", "email": "test@example.com"},
                )

            assert exc_info.value.status == "rejected"
            assert "conflict detected" in str(exc_info.value)
