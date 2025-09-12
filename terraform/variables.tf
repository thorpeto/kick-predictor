variable "project_id" {
  description = "Die Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Die GCP Region für die Deployment"
  type        = string
  default     = "europe-west3"
}

variable "run_service_suffix" {
  description = "Suffix für die Cloud Run Service URL (wird automatisch generiert)"
  type        = string
  default     = "abcdefgh"  # Platzhalter, wird automatisch von GCP ersetzt
}