"""
Created on 1 Jul 2025

@author: ph1jb
Enhanced version of dbcache2.py with structured logging.
"""

from configargparse import Namespace, YAMLConfigFileParser  # type: ignore
from pandas.core.frame import DataFrame
from pathlib import Path
from sqlalchemy import Column, MetaData, String, Table, URL, create_engine, insert, select
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.sql.sqltypes import LargeBinary
from typing import List, Tuple, Dict
import configargparse
import dotenv
import io
import logging
import os
import pandas as pd
import sqlalchemy
import sys
import time
import yaml

metadata_obj = MetaData()

cache_table = Table(
    "cache",
    metadata_obj,
    Column("name", String(255), primary_key=True),
    Column("data", LargeBinary),
)
logger = logging.getLogger(__name__)

# --- Default log format ---
LOGFORMAT = "%(asctime)s %(levelname)s [%(module)s:%(lineno)d] %(funcName)s | %(message)s"


class CacheManager:
    """Manage cache: retrieve from and/or update database cache table."""

    def __init__(self, drivername: str, sqla_options: Dict, config: Namespace):
        self.engine = EngineManager._create_engine_from_sqla_options(
            drivername, sqla_options, config
        )

    def _cache_read(self, table_name: str, con: Connection) -> bytes:
        """Read compressed serialised DataFrame (bytes) from cache. If not present raises exception."""
        logger.debug("Fetching DataFrame for table '%(table_name)s'.", {"table_name": table_name})
        stmt = select(cache_table.c.data).where(cache_table.c.name == table_name)
        result = con.execute(stmt).first()
        if result:
            data = result[0]
            logger.debug("Cache hit for table '%(table_name)s'.", {"table_name": table_name})
            return data
        else:
            logger.debug("Cache miss for '%(table_name)s'. ", {"table_name": table_name})
            return b""

    def _cache_write(self, table_name: str, con: Connection, data: bytes) -> None:
        """Write serialised compressed data to cache.
        Replace into cache to overwrite any existing entry.
        """
        logger.debug("Writing data to cache %(table_name)s", {"table_name": table_name})
        stmt = insert(cache_table).values(name=table_name, data=data)
        # Ignore the exception raised by the mysqlconnector
        # (with options raise_on_warnings=True and use_unicode=True (the default))
        # when writing binary data (which may well contain invalid unicode characters).
        # MySQL emits a warning, the connector raises an exception.
        # However the data is inserted correctly.
        # (The pymysql connector inserts binary data without issue)
        # try:
        con.execute(stmt)
        # except (mysql.connector.errors.DatabaseError, sqlalchemy.exc.DatabaseError) as err:
        #     # When mysql.connector raises a DatabaseError (e.g., mysql.connector.errors.DatabaseError(errno=1300, msg='Invalid utf8mb4 character string')), SQLAlchemy catches it and re-raises it as a sqlalchemy.exc.DatabaseError.
        #     # That DatabaseError wraps the original MySQLConnector exception inside its .orig attribute:
        #     orig = getattr(err, "orig", err)  # unwrap SQLAlchemy wrapper if present
        #     code = getattr(orig, "errno", None)
        #     msg = getattr(orig, "msg", str(orig))
        #     if code == 1300:
        #         logger.debug("Ignored MySQL warning %(code)s: %(msg)s", {"code": code, "msg": msg})
        #         # swallow error and continue
        #     else:
        #         raise
        logger.debug("Wrote data to cache %(table_name)s", {"table_name": table_name})

    def _deserialize_bytes_to_df(self, data: bytes) -> DataFrame:
        """Deserialize gzip-compressed Parquet bytes to a DataFrame."""
        logger.debug(
            "Deserializing cached Parquet data (size=%(size)d bytes).", {"size": len(data)}
        )
        buffer = io.BytesIO(data)
        df = pd.read_parquet(buffer)
        logger.debug(
            "Deserialized DataFrame with %(rows)d rows and %(cols)d columns.",
            {"rows": len(df), "cols": len(df.columns)},
        )
        return df

    def _serialize_df_to_bytes(self, df: pd.DataFrame) -> bytes:
        """Serialize DataFrame to snappy-compressed Parquet bytes."""
        logger.debug(
            "Serializing DataFrame with %(rows)d rows and %(cols)d columns.",
            {"rows": len(df), "cols": len(df.columns)},
        )
        # Parquet cannot handle sqla quoted column names. Convert columns names to string.
        df.columns = [str(c) for c in df.columns]
        data = df.to_parquet(index=False)
        logger.debug("Serialised cached Parquet data (size=%(size)d bytes).", {"size": len(data)})
        return data

    def _table_read(self, table_name: str, con: Connection, **kwargs) -> DataFrame:
        """Read source table into a dataframe.
        kwargs are passed to pd.read_sql.
        See: https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html
        Typically:
        columns: list, default: None
        index_col: str or list of str, optional, default: None
        parse_dates: list or dict, default: None
        """
        logger.debug("Fetching source data table %(table_name)s", {"table_name": table_name})
        df = pd.read_sql(table_name, con, **kwargs)
        logger.debug(
            "Fetched DataFrame with %(rows)d rows and %(cols)d columns.",
            {"rows": len(df), "cols": len(df.columns)},
        )
        return df

    def read_sql_cache(
        self,
        table_name: str,
        con: Connection,
        columns: List[str] | None = None,
        parse_dates: List[str] | None = None,
    ) -> DataFrame:
        """Read and deserialise to DataFrame data from cache if present, otherwise read dataframe from source table, write to cache, return dataframe."""

        # Fetch DataFrame from cache if present
        try:
            logger.debug("Reading data from cache")
            start = time.perf_counter()
            data = self._cache_read(table_name, con)
            end = time.perf_counter()
            logger.info(f"Execution time: {end - start:.6f} seconds")
            if data:
                df = self._deserialize_bytes_to_df(data)
                return df
        except sqlalchemy.exc.ProgrammingError as e:
            logger.info(
                "Cache lookup failed for '%(table_name)s': %(error)s",
                {"table_name": table_name, "error": str(e)},
            )

        # Fetch DataFrame from source table
        try:
            df = self._table_read(table_name, con, columns=columns, parse_dates=parse_dates)

            # Write DataFrame to cache
            data = self._serialize_df_to_bytes(df)
            try:
                self._cache_write(table_name, con, data)
                logger.debug("Wrote data to cache")
            except sqlalchemy.exc.ProgrammingError as e:
                logger.info(
                    "Failed write data to cache '%(table_name)s': %(error)s",
                    {"table_name": table_name, "error": str(e)},
                )
            return df
        except sqlalchemy.exc.ProgrammingError as e:
            logger.info(
                "Failed to read source table '%(table_name)s': %(error)s",
                {"table_name": table_name, "error": str(e)},
            )
            raise


class Config:
    """Load and manage configuration from files, CLI, and environment."""

    def __init__(self, secrets_file: Path) -> None:
        (self.config, unknownargs) = self._parse_config(secrets_file)
        self._setup_logging(fmt=self.config.logformat, level=self.config.loglevel)
        logger.warning("unknownargs %(unknownargs)s", {"unknownargs": unknownargs})

    @staticmethod
    def _parse_config(secrets_file: Path) -> Tuple[Namespace, str]:
        p = configargparse.ArgParser(
            config_file_parser_class=YAMLConfigFileParser,
            default_config_files=[secrets_file],
        )
        p.add(
            "--columns",
            env_var="COLUMNS",
            help="List of columns for pd.read_sql to select: comma separated. Default None (all)",
            type=lambda s: s.split(","),
        )
        p.add(
            "--drivername",
            env_var="DRIVERNAME",
            default="mysql+pymysql",
            help="SQLalchemy driver name. Default: mysql+pymysql ",
        )
        p.add(
            "--loglevel",
            choices=["INFO", "WARNING", "DEBUG", "ERROR", "CRITICAL"],
            default="INFO",
            env_var="LOGLEVEL",
            help="Log level",
        )
        p.add("--logformat", default=LOGFORMAT, env_var="LOGFORMAT", help="Log format")
        p.add("--mysql_database", env_var="MYSQL_DATABASE")
        p.add("--mysql_host", env_var="MYSQL_HOST")
        p.add("--mysql_user", env_var="MYSQL_USER")  # mysql var name
        p.add("--mysql_username", env_var="MYSQL_USERNAME")  # sqlalchemy var name
        p.add("--mysql_password", env_var="MYSQL_PASSWORD")
        p.add(
            "--sqla_options",
            env_var="SQLA_OPTIONS",
            required=True,
            type=yaml.safe_load,
            help="MySQL options",
        )
        p.add(
            "--parse_dates",
            env_var="PARSE_DATES",
            help="List of columns for pd.read_sql to parse as dates, comma separated. Default None.",
            type=lambda s: s.split(","),
        )
        p.add("--table_source", env_var="TABLE_SOURCE", required=True)
        return p.parse_known_args()

    @staticmethod
    def _setup_logging(fmt: str, level: str) -> None:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format=fmt,
            stream=sys.stdout,
        )
        logger.debug("Logging initialized at level %(level)s.", {"level": level})


class EngineManager:
    @staticmethod
    def _create_engine(drivername: str, sqla_options: Dict[str, str | Dict]) -> Engine:
        """Create SQLAlchemy engine from drivername and sqla_options."""
        url = URL.create(drivername, **sqla_options)  # type: ignore
        engine = create_engine(url)
        # Sqlalchemy redacts password
        logger.debug("SQLAlchemy url %(url)s", {"url": url})
        return engine

    @staticmethod
    def _create_engine_from_sqla_options(
        drivername: str, sqla_options: Dict, config: Namespace
    ) -> Engine:
        """Create SQLAlchemy engine from config
        Override mysql_options with mysql_database etc
        Convert mysql_options to Sqlalchemy options
        Create engine with Sqlalchemy drivername and options
        ."""
        EngineManager._sqla_options_override(sqla_options, config)
        return EngineManager._create_engine(drivername, sqla_options)

    @staticmethod
    def _sqla_options_override(sqla_options: Dict[str, str | Dict], config: Namespace):
        """Override the MySQL options based on the provided configuration.
        Updates specific fields: database, host, password, port, user if set in config.
        """
        for k in ("database", "host", "password", "port", "username"):
            v = getattr(config, f"mysql_{k}", None)
            if v:
                sqla_options.update({k: v})


class Main:

    def __init__(self, config: Namespace):
        self.config = config
        # mysql_options = config.mysql_options
        sqla_options = config.sqla_options
        drivername = config.drivername
        self.cache_manager = CacheManager(drivername, sqla_options, config)

    def _run(self):
        """Main entrypoint for cache handling."""
        table_name = self.config.table_source
        logger.debug(
            "Starting data retrieval for table '%(table_name)s'.", {"table_name": table_name}
        )
        columns = self.config.columns
        parse_dates = self.config.parse_dates
        with self.cache_manager.engine.begin() as con:
            self.cache_manager.read_sql_cache(
                table_name, con, columns=columns, parse_dates=parse_dates
            )


if __name__ == "__main__":
    dotenv.load_dotenv(override=True)
    SECRETS_FILE_DEFAULT = (
        Path(__file__).resolve().parent.parent.parent / "secrets" / "dbcache_secrets.yml"
    )
    SECRETS_FILE = Path(os.environ.get("SECRETS_FILE", SECRETS_FILE_DEFAULT))
    CONFIG = Config(SECRETS_FILE)
    MAIN = Main(CONFIG.config)
    MAIN._run()
    logger.debug("Program complete.")
