import pytest

from avatars.config import Config, get_config


class TestConfig:
    """Tests for the Config class."""

    def test_default_avatar_verify_compatibility(self) -> None:
        """Test that AVATAR_VERIFY_COMPATIBILITY defaults to True."""
        config = Config()
        assert config.AVATAR_VERIFY_COMPATIBILITY is True

    def test_avatar_verify_compatibility_from_env_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that AVATAR_VERIFY_COMPATIBILITY can be set to True via env var."""
        monkeypatch.setenv("AVATAR_VERIFY_COMPATIBILITY", "true")
        config = Config()
        assert config.AVATAR_VERIFY_COMPATIBILITY is True

    def test_avatar_verify_compatibility_from_env_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that AVATAR_VERIFY_COMPATIBILITY can be set to False via env var."""
        monkeypatch.setenv("AVATAR_VERIFY_COMPATIBILITY", "false")
        config = Config()
        assert config.AVATAR_VERIFY_COMPATIBILITY is False

    def test_avatar_verify_compatibility_from_env_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test AVATAR_VERIFY_COMPATIBILITY can be set to True via env var with '1'."""
        monkeypatch.setenv("AVATAR_VERIFY_COMPATIBILITY", "1")
        config = Config()
        assert config.AVATAR_VERIFY_COMPATIBILITY is True

    def test_avatar_verify_compatibility_from_env_0(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test AVATAR_VERIFY_COMPATIBILITY can be set to False via env var with '0'."""
        monkeypatch.setenv("AVATAR_VERIFY_COMPATIBILITY", "0")
        config = Config()
        assert config.AVATAR_VERIFY_COMPATIBILITY is False

    def test_get_config(self) -> None:
        """Test the get_config function returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)
        assert hasattr(config, "AVATAR_VERIFY_COMPATIBILITY")
