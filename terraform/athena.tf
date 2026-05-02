resource "aws_athena_workgroup" "analytics" {
  name        = "${local.prefix}-analytics"
  description = "Query staging/curated tables; results land in S3"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake.bucket}/${local.s3_prefixes.athena}/"
    }
  }

  force_destroy = true
}
