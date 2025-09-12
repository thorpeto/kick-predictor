provider "google" {
  project = var.project_id
  region  = var.region
}

# Aktiviere benötigte API Services
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "containerregistry.googleapis.com",
    "cloudbuild.googleapis.com",
  ])
  project = var.project_id
  service = each.key

  disable_on_destroy = false
}

# Backend Cloud Run Service
resource "google_cloud_run_service" "backend" {
  name     = "kick-predictor-backend"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/kick-predictor-backend:latest"
        
        env {
          name  = "ENVIRONMENT"
          value = "production"
        }

        env {
          name  = "ALLOWED_ORIGINS"
          value = "https://kick-predictor-frontend-${var.run_service_suffix}.a.run.app"
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "5"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.services]
}

# Public Zugriff auf Backend erlauben
resource "google_cloud_run_service_iam_member" "backend_public" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Frontend Cloud Run Service
resource "google_cloud_run_service" "frontend" {
  name     = "kick-predictor-frontend"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/kick-predictor-frontend:latest"
        
        env {
          name  = "NODE_ENV"
          value = "production"
        }

        env {
          name  = "BACKEND_URL"
          value = google_cloud_run_service.backend.status[0].url
        }

        resources {
          limits = {
            cpu    = "500m"
            memory = "256Mi"
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "3"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.services,
    google_cloud_run_service.backend
  ]
}

# Public Zugriff auf Frontend erlauben
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_service.frontend.name
  location = google_cloud_run_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output der URLs für den Zugriff
output "backend_url" {
  value = google_cloud_run_service.backend.status[0].url
}

output "frontend_url" {
  value = google_cloud_run_service.frontend.status[0].url
}