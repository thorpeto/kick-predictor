# Kostenschätzung für GCP Deployment

## Cloud Run (Empfohlene Option)

### Backend
- **CPU**: 1 vCPU
- **Memory**: 1 GB
- **Requests**: ~1000/Monat (geschätzt)
- **Kosten**: ~€5-10/Monat

### Frontend  
- **CPU**: 1 vCPU
- **Memory**: 512 MB
- **Requests**: ~5000/Monat (geschätzt)
- **Kosten**: ~€10-15/Monat

### Container Registry
- **Storage**: ~2 GB (Images)
- **Kosten**: ~€0.10/Monat

### Gesamtkosten Cloud Run: €15-25/Monat

## Alternative: App Engine

### Standard Environment
- **Backend**: F2 Instance (~€35/Monat)
- **Frontend**: F1 Instance (~€25/Monat)
- **Gesamtkosten**: €60/Monat

## Datenbank-Optionen

### Option 1: SQLite + Cloud Storage (Empfohlen für Start)
- **Storage**: 1 GB
- **Operations**: 1000/Monat
- **Kosten**: ~€0.05/Monat

### Option 2: Cloud SQL PostgreSQL
- **db-f1-micro**: €7/Monat
- **db-g1-small**: €25/Monat
- **Storage**: €0.17/GB/Monat

## Zusätzliche Services

### Cloud Scheduler (für Auto-Updates)
- **Jobs**: 3 Jobs (täglich)
- **Kosten**: €0.10/Monat

### Cloud Monitoring
- **Basic**: Kostenlos
- **Advanced**: €0.20/GB Logs

## Empfohlenes Setup für Start

```
✅ Cloud Run Backend (1 GB)      €8/Monat
✅ Cloud Run Frontend (512 MB)   €12/Monat  
✅ Container Registry            €0.10/Monat
✅ Cloud Storage (SQLite)        €0.05/Monat
✅ Cloud Scheduler              €0.10/Monat
─────────────────────────────────────────
Total: ~€20/Monat
```

## Skalierung und Traffic

### Bei 10.000 Requests/Monat:
- Cloud Run: €30-40/Monat
- App Engine: €80-100/Monat

### Bei 100.000 Requests/Monat:
- Cloud Run: €100-150/Monat  
- App Engine: €200-300/Monat

## Kostenoptimierung-Tipps

1. **Cloud Run Concurrency**: Auf 80-100 setzen
2. **Min Instances**: Auf 0 für minimale Kosten
3. **CPU Allocation**: "CPU allocated only during request processing"
4. **Monitoring**: Budgets und Alerts einrichten
5. **Images**: Multi-stage builds für kleinere Images

## Free Tier Limits (immer verfügbar)

- **Cloud Run**: 2 Millionen Requests/Monat
- **Container Registry**: 0.5 GB Storage  
- **Cloud Storage**: 5 GB
- **Cloud Build**: 120 Build-Minuten/Tag

Mit dem Free Tier können Sie die App praktisch kostenlos hosten, wenn der Traffic niedrig bleibt!