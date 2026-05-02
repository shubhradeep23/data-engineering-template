data "aws_caller_identity" "current" {}

locals {
  prefix = "${var.project_name}-${var.environment}"

  s3_prefixes = {
    raw     = "raw"
    staging = "staging"
    curated = "curated"
    scripts = "glue-scripts"
    athena  = "athena-results"
  }
}
