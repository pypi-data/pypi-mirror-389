"""Tests for GitStorage client."""

import base64
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from pierre_storage import GitStorage, create_client, generate_jwt
from pierre_storage.errors import ApiError


class TestGitStorage:
    """Tests for GitStorage class."""

    def test_create_instance(self, git_storage_options: dict) -> None:
        """Test creating GitStorage instance."""
        storage = GitStorage(git_storage_options)
        assert storage is not None
        assert isinstance(storage, GitStorage)

    def test_store_key(self, git_storage_options: dict, test_key: str) -> None:
        """Test that key is stored."""
        storage = GitStorage(git_storage_options)
        config = storage.get_config()
        assert config["key"] == test_key

    def test_missing_options(self) -> None:
        """Test error when options are missing."""
        with pytest.raises(ValueError, match="GitStorage requires a name and key"):
            GitStorage({})  # type: ignore

    def test_null_key(self, test_key: str) -> None:
        """Test error when key is null."""
        with pytest.raises(ValueError, match="GitStorage requires a name and key"):
            GitStorage({"name": "test", "key": None})  # type: ignore

    def test_empty_key(self) -> None:
        """Test error when key is empty."""
        with pytest.raises(ValueError, match="GitStorage key must be a non-empty string"):
            GitStorage({"name": "test", "key": ""})

    def test_empty_name(self, test_key: str) -> None:
        """Test error when name is empty."""
        with pytest.raises(ValueError, match="GitStorage name must be a non-empty string"):
            GitStorage({"name": "", "key": test_key})

    def test_whitespace_key(self) -> None:
        """Test error when key is whitespace."""
        with pytest.raises(ValueError, match="GitStorage key must be a non-empty string"):
            GitStorage({"name": "test", "key": "   "})

    def test_whitespace_name(self, test_key: str) -> None:
        """Test error when name is whitespace."""
        with pytest.raises(ValueError, match="GitStorage name must be a non-empty string"):
            GitStorage({"name": "   ", "key": test_key})

    def test_non_string_key(self) -> None:
        """Test error when key is not a string."""
        with pytest.raises(ValueError, match="GitStorage key must be a non-empty string"):
            GitStorage({"name": "test", "key": 123})  # type: ignore

    def test_non_string_name(self, test_key: str) -> None:
        """Test error when name is not a string."""
        with pytest.raises(ValueError, match="GitStorage name must be a non-empty string"):
            GitStorage({"name": 123, "key": test_key})  # type: ignore

    @pytest.mark.asyncio
    async def test_create_repo(self, git_storage_options: dict) -> None:
        """Test creating a repository."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"repo_id": "test-repo", "url": "https://test.git"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo(id="test-repo")
            assert repo is not None
            assert repo.id == "test-repo"

    @pytest.mark.asyncio
    async def test_create_repo_with_base_repo(self, git_storage_options: dict) -> None:
        """Test creating a repository with GitHub sync."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"repo_id": "test-repo", "url": "https://test.git"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            repo = await storage.create_repo(
                id="test-repo",
                base_repo={
                    "owner": "octocat",
                    "name": "Hello-World",
                    "default_branch": "main",
                }
            )
            assert repo is not None
            assert repo.id == "test-repo"

            # Verify the request was made with base_repo in the body
            call_kwargs = mock_post.call_args[1]
            body = call_kwargs["json"]
            assert "base_repo" in body
            assert body["base_repo"]["provider"] == "github"
            assert body["base_repo"]["owner"] == "octocat"
            assert body["base_repo"]["name"] == "Hello-World"
            assert body["base_repo"]["default_branch"] == "main"

    @pytest.mark.asyncio
    async def test_create_repo_with_base_repo_forces_github_provider(
        self, git_storage_options: dict
    ) -> None:
        """Test that base_repo forces provider to 'github'."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Create repo without provider in base_repo
            await storage.create_repo(
                id="test-repo",
                base_repo={
                    "owner": "octocat",
                    "name": "Hello-World",
                }
            )

            # Verify provider was forced to 'github'
            call_kwargs = mock_post.call_args[1]
            body = call_kwargs["json"]
            assert body["base_repo"]["provider"] == "github"

    @pytest.mark.asyncio
    async def test_create_repo_conflict(self, git_storage_options: dict) -> None:
        """Test creating a repository that already exists."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.is_success = False

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(ApiError, match="Repository already exists"):
                await storage.create_repo(id="existing-repo")

    @pytest.mark.asyncio
    async def test_find_one(self, git_storage_options: dict) -> None:
        """Test finding a repository."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"id": "test-repo"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.find_one(id="test-repo")
            assert repo is not None
            assert repo.id == "test-repo"

    @pytest.mark.asyncio
    async def test_find_one_not_found(self, git_storage_options: dict) -> None:
        """Test finding a repository that doesn't exist."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.is_success = False

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.find_one(id="nonexistent")
            assert repo is None

    def test_create_client_factory(self, git_storage_options: dict) -> None:
        """Test create_client factory function."""
        client = create_client(git_storage_options)
        assert isinstance(client, GitStorage)


class TestJWTGeneration:
    """Tests for JWT generation."""

    @pytest.mark.asyncio
    async def test_jwt_structure(self, git_storage_options: dict, test_key: str) -> None:
        """Test JWT has correct structure."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo(id="test-repo")
            url = await repo.get_remote_url()

            # Extract JWT from URL
            import re

            match = re.search(r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\.git", url)
            assert match is not None
            token = match.group(1)

            # Decode JWT (without verification for testing)
            payload = jwt.decode(token, options={"verify_signature": False})

            assert payload["iss"] == "test-customer"
            assert payload["sub"] == "@pierre/storage"
            assert payload["repo"] == "test-repo"
            assert "scopes" in payload
            assert "iat" in payload
            assert "exp" in payload
            assert payload["exp"] > payload["iat"]

    @pytest.mark.asyncio
    async def test_jwt_default_permissions(self, git_storage_options: dict) -> None:
        """Test JWT has default permissions."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo(id="test-repo")
            url = await repo.get_remote_url()

            # Extract and decode JWT
            import re

            match = re.search(r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\.git", url)
            token = match.group(1)
            payload = jwt.decode(token, options={"verify_signature": False})

            assert payload["scopes"] == ["git:write", "git:read"]

    @pytest.mark.asyncio
    async def test_jwt_custom_permissions(self, git_storage_options: dict) -> None:
        """Test JWT with custom permissions."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo(id="test-repo")
            url = await repo.get_remote_url(permissions=["git:read"], ttl=3600)

            # Extract and decode JWT
            import re

            match = re.search(r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\.git", url)
            token = match.group(1)
            payload = jwt.decode(token, options={"verify_signature": False})

            assert payload["scopes"] == ["git:read"]
            assert payload["exp"] - payload["iat"] == 3600

    @pytest.mark.asyncio
    async def test_get_ephemeral_remote_url(self, git_storage_options: dict) -> None:
        """Test getting ephemeral remote URL."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo(id="test-repo")
            url = await repo.get_ephemeral_remote_url()

            # Verify URL has +ephemeral.git suffix
            assert url.endswith("+ephemeral.git")
            assert "test-repo+ephemeral.git" in url

    @pytest.mark.asyncio
    async def test_get_ephemeral_remote_url_with_permissions(self, git_storage_options: dict) -> None:
        """Test ephemeral remote URL with custom permissions."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo(id="test-repo")
            url = await repo.get_ephemeral_remote_url(permissions=["git:read"], ttl=3600)

            # Verify URL structure
            assert url.endswith("+ephemeral.git")

            # Extract and decode JWT
            import re

            match = re.search(r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\+ephemeral\.git", url)
            assert match is not None
            token = match.group(1)
            payload = jwt.decode(token, options={"verify_signature": False})

            assert payload["scopes"] == ["git:read"]
            assert payload["exp"] - payload["iat"] == 3600

    @pytest.mark.asyncio
    async def test_ephemeral_url_structure(self, git_storage_options: dict) -> None:
        """Test that get_ephemeral_remote_url has correct URL structure."""
        storage = GitStorage(git_storage_options)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            repo = await storage.create_repo(id="test-repo")
            ephemeral_url = await repo.get_ephemeral_remote_url(permissions=["git:write"], ttl=1800)

            # Verify URL structure
            import re

            match = re.search(
                r"https://t:(.+)@test-customer\.test\.code\.storage/test-repo\+ephemeral\.git",
                ephemeral_url
            )
            assert match is not None, f"URL doesn't match expected pattern: {ephemeral_url}"

            # Verify JWT has correct scopes and TTL
            token = match.group(1)
            payload = jwt.decode(token, options={"verify_signature": False})
            assert payload["scopes"] == ["git:write"]
            assert payload["exp"] - payload["iat"] == 1800


class TestPublicJWTHelper:
    """Tests for publicly exported generate_jwt function."""

    def test_generate_jwt_basic(self, test_key: str) -> None:
        """Test basic JWT generation with public helper."""
        token = generate_jwt(
            key_pem=test_key,
            issuer="test-customer",
            repo_id="test-repo",
        )

        # Decode and verify structure
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["iss"] == "test-customer"
        assert payload["sub"] == "@pierre/storage"
        assert payload["repo"] == "test-repo"
        assert payload["scopes"] == ["git:write", "git:read"]
        assert "iat" in payload
        assert "exp" in payload

    def test_generate_jwt_with_custom_scopes(self, test_key: str) -> None:
        """Test JWT generation with custom scopes."""
        token = generate_jwt(
            key_pem=test_key,
            issuer="test-customer",
            repo_id="test-repo",
            scopes=["git:read"],
        )

        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["scopes"] == ["git:read"]

    def test_generate_jwt_with_custom_ttl(self, test_key: str) -> None:
        """Test JWT generation with custom TTL."""
        ttl = 3600
        token = generate_jwt(
            key_pem=test_key,
            issuer="test-customer",
            repo_id="test-repo",
            ttl=ttl,
        )

        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["exp"] - payload["iat"] == ttl

    def test_generate_jwt_with_all_parameters(self, test_key: str) -> None:
        """Test JWT generation with all parameters specified."""
        token = generate_jwt(
            key_pem=test_key,
            issuer="my-company",
            repo_id="my-repo-123",
            scopes=["git:write", "git:read", "repo:write"],
            ttl=7200,
        )

        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["iss"] == "my-company"
        assert payload["repo"] == "my-repo-123"
        assert payload["scopes"] == ["git:write", "git:read", "repo:write"]
        assert payload["exp"] - payload["iat"] == 7200

    def test_generate_jwt_default_ttl(self, test_key: str) -> None:
        """Test JWT generation uses 1 year default TTL."""
        token = generate_jwt(
            key_pem=test_key,
            issuer="test-customer",
            repo_id="test-repo",
        )

        payload = jwt.decode(token, options={"verify_signature": False})
        # Default TTL is 1 year (31536000 seconds)
        assert payload["exp"] - payload["iat"] == 31536000

    def test_generate_jwt_invalid_key(self) -> None:
        """Test JWT generation with invalid key."""
        with pytest.raises(ValueError, match="Failed to load private key"):
            generate_jwt(
                key_pem="invalid-key",
                issuer="test-customer",
                repo_id="test-repo",
            )

    def test_generate_jwt_signature_valid(self, test_key: str) -> None:
        """Test that generated JWT signature can be verified."""
        from cryptography.hazmat.primitives import serialization

        # Generate token
        token = generate_jwt(
            key_pem=test_key,
            issuer="test-customer",
            repo_id="test-repo",
        )

        # Load public key for verification
        private_key = serialization.load_pem_private_key(
            test_key.encode("utf-8"),
            password=None,
        )
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Verify signature
        payload = jwt.decode(
            token,
            public_pem,
            algorithms=["ES256"],
        )

        assert payload["iss"] == "test-customer"
        assert payload["repo"] == "test-repo"
