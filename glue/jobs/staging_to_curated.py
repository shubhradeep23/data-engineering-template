"""
Glue 4.0 / Spark: staging Parquet -> curated aggregates for analytics / serving.
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
        "STAGING_BUCKET",
        "STAGING_PREFIX",
        "CURATED_BUCKET",
        "CURATED_PREFIX",
    ],
)

sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

staging_uri = f"s3://{args['STAGING_BUCKET']}/{args['STAGING_PREFIX']}/"
curated_uri = f"s3://{args['CURATED_BUCKET']}/{args['CURATED_PREFIX']}/"

df = spark.read.parquet(staging_uri)

group_cols = ["dt"]
for extra in ("source", "name", "fall"):
    if extra in df.columns and extra not in group_cols:
        group_cols.append(extra)

agg_exprs = [F.count(F.lit(1)).alias("row_count")]
if "event_id" in df.columns:
    agg_exprs.append(F.countDistinct("event_id").alias("distinct_event_id"))
elif "id" in df.columns:
    agg_exprs.append(F.countDistinct("id").alias("distinct_id"))

summary = df.groupBy(*group_cols).agg(*agg_exprs)

summary.write.mode("overwrite").partitionBy("dt").parquet(curated_uri)

job.commit()
