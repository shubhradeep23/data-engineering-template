resource "aws_iam_role_policy" "eventbridge_start_glue" {
  count = var.enable_eventbridge_trigger ? 1 : 0
  name  = "${local.prefix}-evbridge-start-glue"
  role  = aws_iam_role.eventbridge_glue[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "glue:StartJobRun"
      ]
      Resource = [
        aws_glue_job.raw_to_staging.arn
      ]
    }]
  })
}

resource "aws_cloudwatch_event_rule" "raw_object_created" {
  count       = var.enable_eventbridge_trigger ? 1 : 0
  name        = "${local.prefix}-s3-raw-object-created"
  description = "Object Created events for raw/ prefix"
  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [aws_s3_bucket.data_lake.bucket] }
      object = { key = [{ prefix = "raw/" }] }
    }
  })
}

resource "aws_cloudwatch_event_target" "start_raw_to_staging" {
  count     = var.enable_eventbridge_trigger ? 1 : 0
  rule      = aws_cloudwatch_event_rule.raw_object_created[0].name
  target_id = "StartGlueRawToStaging"
  arn       = aws_glue_job.raw_to_staging.arn
  role_arn  = aws_iam_role.eventbridge_glue[0].arn

  glue_target {
    job_name = aws_glue_job.raw_to_staging.name
  }

  depends_on = [aws_iam_role_policy.eventbridge_start_glue]
}
