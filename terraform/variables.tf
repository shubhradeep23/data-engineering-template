variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Short name used in resource names (lowercase, no spaces)."
  default     = "de-template"
}

variable "environment" {
  type        = string
  description = "Environment label (e.g. dev, prod)."
  default     = "dev"
}

variable "enable_eventbridge_trigger" {
  type        = bool
  description = "If true, new objects under raw/ start the raw_to_staging Glue job via EventBridge (may increase cost)."
  default     = false
}

variable "glue_worker_type" {
  type        = string
  description = "Glue worker type for Spark jobs (e.g. G.1X)."
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  type        = number
  description = "Number of Glue workers (minimum 2 for G.1X in many regions)."
  default     = 2
}
