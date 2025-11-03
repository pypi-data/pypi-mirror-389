import logging

from delta.tables import *
from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window

from .common import *
from .repo import M

_logger = logging.getLogger(__name__)
S, Q, _ = M.get_instance()
_DB = "emdm"
_FMT = "delta"
_FILE = "s3a://emdm/{}/table"
_JVM = S._jvm  # type: ignore
_JSC = S._jsc  # type: ignore
_CATA = S.catalog  # type: ignore


def NDS_import_data(data):
    assert S is not None
    return data if hasattr(data, "schema") else S.createDataFrame(data)


def NDS_exist_table(file):
    try:
        fs = _JVM.org.apache.hadoop.fs.FileSystem.get(
            _JSC.hadoopConfiguration())
        return fs.exists(_JVM.org.apache.hadoop.fs.Path(f"{file}/{NDS_LOG_NAME}"))
    except Exception:
        return None


def NDS_describe_table(table: str, fmt=_FMT) -> list[dict]:
    assert S is not None
    df = S.table(table) if NDS_is_table_or_db(
        table) else S.read.format(fmt).load(table)
    return [{"col_name": f.name,
             "data_type": str(f.dataType),
             "comment": f.metadata.get("comment", "")}
            for f in df.schema.fields
            ]


def NDS_list_tables(db: str):
    if NDS_is_table_or_db(db):
        return [{"tableName": f"{db}.{t.name}"} for t in _CATA.listTables(db)]

    tables = []
    path = _JVM.org.apache.hadoop.fs.Path(db)
    fs = path.getFileSystem(_JSC.hadoopConfiguration())

    for s in fs.listStatus(path):
        if s.isDirectory():
            table = str(s.getPath().toString())
            try:
                if NDS_exist_table(table):
                    tables.append(table)
            except Exception:
                continue
    return [{"tableName": t} for t in tables]


def NDS_query_table(table: str, fields: str, body: dict):
    filters: str = body.get("filters", "")
    page: int = int(body.get("page", 1))
    page_size: int = int(body.get("page_size", 20))

    q = "SELECT {} FROM {}".format(fields, table)
    if filters:
        q += f" WHERE {filters}"

    NDS_check_table(q)
    data = Q(q)

    start = (page - 1) * page_size
    end = start + page_size
    total = data.count()
    rows = data.collect()
    return {"rows": [row.asDict() for row in rows[start:end]], "total": total}


def NDS_execute(data=None, keys=None, branch: str = "main", file: str = "", db: str = _DB, fmt: str = _FMT):
    if not data:
        return

    if not file:
        file = _FILE.format(branch)

    table = NDS_get_table(file)
    table = f"{db}.{table}"
    data = NDS_import_data(data)
    _logger.debug(data.head())

    try:
        if not _CATA.databaseExists(db):
            _CATA.createDatabase(db)
        _CATA.setCurrentDatabase(db)

        _logger.info(f"save to {file}")
        if keys and NDS_exist_table(file):
            _logger.info(f"keys: {keys}")
            condition = " AND ".join([f"d.{k} = s.{k}" for k in keys])
            delta_table = DeltaTable.forPath(S, file)
            (delta_table.alias("d")
             .merge(data.alias("s"), condition)
             .whenMatchedUpdateAll()
             .whenNotMatchedInsertAll()
             .execute())
            _CATA.refreshTable(table)
            return table

        Q(f"DROP TABLE IF EXISTS {table}")
        (data.write.mode("overwrite")
            .option("overwriteSchema", "true")
            .option("path", file)
            .format(fmt)
            .saveAsTable(table))
        return table
    except Exception as e:
        _logger.exception("error")
