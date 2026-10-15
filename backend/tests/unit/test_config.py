from app.config import Settings


def test_default_settings():
    settings = Settings(
        app_env="test",
        graph_backend="local",
        max_concurrent_agents=5,
    )
    assert settings.app_env == "test"
    assert settings.graph_backend == "local"
    assert settings.max_concurrent_agents == 5
    assert settings.falkordb_port == 6379


def test_falkordb_settings():
    settings = Settings(
        graph_backend="falkordb",
        falkordb_host="cloud.falkordb.com",
        falkordb_port=6379,
        falkordb_password="secret-password",
    )
    assert settings.graph_backend == "falkordb"
    assert settings.falkordb_host == "cloud.falkordb.com"
    assert settings.falkordb_password == "secret-password"
