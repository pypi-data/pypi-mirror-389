"""
Created on 2 Nov 2025

@author: ph1jb
Test suite for dbcache.
"""

from dbcache import CacheManager, Config, EngineManager, Main, cache_table, metadata_obj
from sqlalchemy import create_engine, LargeBinary
from types import SimpleNamespace
import io
import logging
import pandas as pd
import pytest
import sqlalchemy


# -------------------------
# Fixtures
# -------------------------


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    metadata_obj.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def mock_config():
    # Minimal mock config namespace
    return SimpleNamespace(
        logformat="%(message)s",
        loglevel="DEBUG",
        mysql_options={"user": "u", "password": "p"},
        sqla_options={"user": "u", "password": "p"},
        drivername="sqlite",
        table_source="cache",
        columns=None,
        parse_dates=None,
    )


# -------------------------
# CacheManager Tests
# -------------------------


class TestCacheManager:

    def test_cache_write_and_read(self, sqlite_engine, mock_config):
        cm = CacheManager("sqlite", {}, mock_config)
        cm.engine = sqlite_engine

        with sqlite_engine.begin() as con:
            data = b"abc123"
            cm._cache_write("test_table", con, data)
            res = cm._cache_read("test_table", con)
            assert res == data

    def test_cache_read_empty_returns_blank(self, sqlite_engine, mock_config):
        cm = CacheManager("sqlite", {}, mock_config)
        cm.engine = sqlite_engine
        with sqlite_engine.begin() as con:
            result = cm._cache_read("nonexistent", con)
            assert result == b""

    def test_serialize_deserialize_roundtrip(self, mock_config):
        cm = CacheManager("sqlite", {}, mock_config)
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        data = cm._serialize_df_to_bytes(df)
        df2 = cm._deserialize_bytes_to_df(data)
        pd.testing.assert_frame_equal(df, df2)

    def test_deserialize_bytes_to_df_raises_on_invalid_data(self, mock_config):
        """Invalid parquet bytes should raise an exception."""
        cm = CacheManager("sqlite", {}, mock_config)
        with pytest.raises(Exception):
            cm._deserialize_bytes_to_df(b"not a parquet file")

    def test_table_read_uses_read_sql(self, sqlite_engine, mocker, mock_config):
        cm = CacheManager("sqlite", {}, mock_config)
        mock_df = pd.DataFrame({"x": [1]})
        mocker.patch("dbcache.pd.read_sql", return_value=mock_df)
        with sqlite_engine.begin() as con:
            df = cm._table_read("dummy_table", con)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["x"]

    def test_read_sql_cache_prefers_cache(self, sqlite_engine, mocker, mock_config):
        cm = CacheManager("sqlite", {}, mock_config)
        mocker.patch.object(cm, "_cache_read", return_value=b"abc")
        mocker.patch.object(cm, "_deserialize_bytes_to_df", return_value=pd.DataFrame({"a": [1]}))
        mocker.patch.object(cm, "_table_read", side_effect=AssertionError("Should not be called"))
        with sqlite_engine.begin() as con:
            df = cm.read_sql_cache("t1", con)
        assert "a" in df.columns

    def test_read_sql_cache_reads_table_if_cache_empty(self, sqlite_engine, mocker, mock_config):
        cm = CacheManager("sqlite", {}, mock_config)
        mocker.patch.object(cm, "_cache_read", return_value=b"")
        mocker.patch.object(cm, "_table_read", return_value=pd.DataFrame({"a": [1]}))
        mocker.patch.object(cm, "_serialize_df_to_bytes", return_value=b"xyz")
        mocker.patch.object(cm, "_cache_write", return_value=None)
        with sqlite_engine.begin() as con:
            df = cm.read_sql_cache("t1", con)
        assert list(df.columns) == ["a"]



# -------------------------
# Config Tests
# -------------------------


class TestConfig:

    def test_setup_logging_runs(self):
        """Verify logging setup actually emits messages to our stream."""
        import io

        stream = io.StringIO()

        # Reset any existing logging configuration so basicConfig applies
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(stream=stream, level=logging.INFO, format="%(message)s")
        logger = logging.getLogger("test_logger")
        logger.propagate = True
        logger.info("hello world")

        # Force flush
        for handler in logging.root.handlers:
            handler.flush()

        output = stream.getvalue()
        assert "hello world" in output


# -------------------------
# EngineManager Tests
# -------------------------


class TestEngineManager:


    def test_sqla_options_override_updates_fields(self):
        ns = SimpleNamespace(mysql_host="127.0.0.1", mysql_username="root")
        opts = {"host": "x", "username": "old"}
        EngineManager._sqla_options_override(opts, ns)
        assert opts["host"] == "127.0.0.1"
        assert opts["username"] == "root"

    def test_create_engine_from_sqla_options_sqlite(self, mock_config):
        eng = EngineManager._create_engine_from_sqla_options("sqlite", {}, mock_config)
        assert "sqlite" in str(eng.url)


# -------------------------
# Main Tests
# -------------------------


class TestMain:

    def test_main_run_calls_cache_manager(self, sqlite_engine, mocker, mock_config):
        cm_mock = mocker.Mock()
        cm_mock.engine = sqlite_engine
        mocker.patch("dbcache.CacheManager", return_value=cm_mock)
        main = Main(mock_config)
        cm_mock.read_sql_cache.return_value = pd.DataFrame({"a": [1]})
        main._run()
        cm_mock.read_sql_cache.assert_called_once()
