"""
Glue 4.0 / Spark: JSON (raw) -> Parquet (staging), partitioned by dt.
Handles semi-structured logs or array-derived JSONL with varying columns.
"""
import sys

from awsglue.utils import getResolvedOptions
from awsglue.job import Job
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "RAW_BUCKET",
        "RAW_PREFIX",
        "STAGING_BUCKET",
        "STAGING_PREFIX",
    ],
)

sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

raw_uri = f"s3://{args['RAW_BUCKET']}/{args['RAW_PREFIX']}/"
staging_uri = f"s3://{args['STAGING_BUCKET']}/{args['STAGING_PREFIX']}/"

df = spark.read.option("multiLine", "false").json(raw_uri)

columns = set(df.columns)

if "timestamp" in columns and "event_ts" not in columns:
    df = df.withColumnRenamed("timestamp", "event_ts")

if "event_ts" in df.columns:
    df = df.withColumn("dt", F.to_date(F.to_timestamp(F.col("event_ts"))))
elif "year" in df.columns:
    df = df.withColumn(
        "dt",
        F.to_date(F.concat_ws("-", F.col("year").cast("string"), F.lit("01"), F.lit("01"))),
    )
else:
    df = df.withColumn("dt", F.current_date())

df.write.mode("overwrite").partitionBy("dt").parquet(staging_uri)

job.commit()
