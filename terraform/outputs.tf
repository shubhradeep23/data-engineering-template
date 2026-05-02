output "data_lake_bucket" {
  description = "S3 data lake bucket name"
  value       = aws_s3_bucket.data_lake.bucket
}

output "s3_prefixes" {
  description = "Key prefixes for raw, staging, curated, scripts, Athena results"
  value       = local.s3_prefixes
}

output "glue_catalog_database" {
  description = "Glue Data Catalog database name"
  value       = aws_glue_catalog_database.lake.name
}

output "glue_job_raw_to_staging" {
  description = "Glue ETL job: raw JSON -> staging Parquet"
  value       = aws_glue_job.raw_to_staging.name
}

output "glue_job_staging_to_curated" {
  description = "Glue ETL job: staging -> curated aggregates"
  value       = aws_glue_job.staging_to_curated.name
}

output "glue_crawler_staging" {
  description = "Run after raw_to_staging to register staging Parquet tables"
  value       = aws_glue_crawler.staging.name
}

output "glue_crawler_curated" {
  description = "Run after staging_to_curated to register curated Parquet tables"
  value       = aws_glue_crawler.curated.name
}

output "athena_workgroup" {
  description = "Athena workgroup for serving-layer SQL"
  value       = aws_athena_workgroup.analytics.name
}

output "eventbridge_trigger_enabled" {
  description = "Whether uploads to raw/ auto-start the first Glue job"
  value       = var.enable_eventbridge_trigger
}
