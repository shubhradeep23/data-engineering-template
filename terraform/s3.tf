resource "aws_s3_bucket" "data_lake" {
  bucket = "${local.prefix}-data-lake-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "glue_script_raw_to_staging" {
  bucket = aws_s3_bucket.data_lake.bucket
  key    = "${local.s3_prefixes.scripts}/raw_to_staging.py"
  source = "${path.module}/../glue/jobs/raw_to_staging.py"
  etag   = filemd5("${path.module}/../glue/jobs/raw_to_staging.py")
}

resource "aws_s3_object" "glue_script_staging_to_curated" {
  bucket = aws_s3_bucket.data_lake.bucket
  key    = "${local.s3_prefixes.scripts}/staging_to_curated.py"
  source = "${path.module}/../glue/jobs/staging_to_curated.py"
  etag   = filemd5("${path.module}/../glue/jobs/staging_to_curated.py")
}

resource "aws_s3_bucket_notification" "eventbridge" {
  count       = var.enable_eventbridge_trigger ? 1 : 0
  bucket      = aws_s3_bucket.data_lake.id
  eventbridge = true

  depends_on = [aws_s3_bucket_server_side_encryption_configuration.data_lake]
}
