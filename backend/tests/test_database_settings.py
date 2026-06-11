import pytest

from config.settings import build_database_config


def test_database_config_uses_existing_split_postgres_variables():
    config = build_database_config(
        {
            "POSTGRES_DB": "neondb",
            "POSTGRES_USER": "neondb_owner",
            "POSTGRES_PASSWORD": "test-password",
            "POSTGRES_HOST": "ep-example.eu-west-2.aws.neon.tech",
            "POSTGRES_PORT": "5432",
        }
    )

    assert config == {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "neondb",
            "USER": "neondb_owner",
            "PASSWORD": "test-password",
            "HOST": "ep-example.eu-west-2.aws.neon.tech",
            "PORT": "5432",
        }
    }


def test_database_config_omits_ssl_options_by_default():
    assert "OPTIONS" not in build_database_config({})["default"]


def test_database_config_does_not_mutate_supplied_environment():
    env = {"POSTGRES_DB": "neondb", "POSTGRES_SSL_REQUIRE": "true"}

    build_database_config(env)

    assert env == {"POSTGRES_DB": "neondb", "POSTGRES_SSL_REQUIRE": "true"}


@pytest.mark.parametrize("truthy_value", ["1", "true", "TRUE", "yes", "on"])
def test_database_config_requires_ssl_for_truthy_values(truthy_value):
    config = build_database_config({"POSTGRES_SSL_REQUIRE": truthy_value})

    assert config["default"]["OPTIONS"] == {"sslmode": "require"}
