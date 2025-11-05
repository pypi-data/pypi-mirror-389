_SEP = "/"
_PATH = "://"
_SQL_SEP = ";"
_C = {
    "spark.hadoop.fs.defaultFS": "s3a://emdm/main",
    "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
    "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    "spark.sql.catalogImplementation": "hive",
    "spark.sql.warehouse.dir": "s3a://emdm/main/spark-warehouse",
    "spark.databricks.hive.metastore.schema.syncOnWrite": "true",
    "spark.databricks.delta.logRetentionDuration": "interval 1 days",
    "spark.databricks.delta.schema.autoMerge.enabled": "true",
    "spark.databricks.delta.properties.defaults.columnMapping.mode": "name",
    "spark.databricks.delta.optimizeWrite.enabled": "true",
    "spark.databricks.delta.autoCompact.maxFileSize": "134217728",
}
NDS_LOG_NAME = "_delta_log"


def NDS_get_table(file):
    return file.rstrip(_SEP).split(_SEP)[-1].lower()


def NDS_is_table_or_db(s: str):
    return _PATH not in s


def NDS_check_table(statement):
    if _SQL_SEP in statement:
        raise ValueError("Illegal statement: {}".format(statement))


def NDS_get_instance(session):
    builder = session.builder
    app = builder.appName("NDS")
    for k, v in _C.items():
        app = app.config(k, v)
    return app.getOrCreate()
