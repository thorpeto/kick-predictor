# Railway Deployment mit PostgreSQL

## 1. requirements.txt erweitern:
```
psycopg2-binary>=2.9.7  # PostgreSQL adapter
```

## 2. database/config.py anpassen:
```python
def __init__(self):
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        if database_url.startswith('postgres://'):
            # Railway/Heroku compatibility
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        self.database_url = database_url
    else:
        # Local development fallback
        self.database_url = "sqlite:///./kick_predictor.db"
```

## 3. Models bleiben identisch:
- SQLAlchemy funktioniert mit PostgreSQL genauso
- Migrations automatisch mit alembic
- Keine Code-Änderungen nötig

## 4. Deployment-Commands:
```bash
# Add PostgreSQL dependency
echo "psycopg2-binary>=2.9.7" >> backend/requirements.txt

# Commit & push
git add .
git commit -m "Add PostgreSQL support for Railway"
git push origin main

# Deploy on Railway
# 1. Connect GitHub repo
# 2. Add PostgreSQL service  
# 3. Set DATABASE_URL variable
# 4. Deploy!
```

## Erwartete Performance:
- ✅ Database-Init: ~2-3 Sekunden
- ✅ API Response: ~50-100ms  
- ✅ Persistent data über Restarts
- ✅ Automatische Backups
- ✅ 500MB Storage kostenlos

## Alternative: Neon + Vercel
```bash
# 1. Neon Database erstellen (3GB free)
# 2. Vercel Frontend + API Routes
# 3. DATABASE_URL als Environment Variable
# 4. Noch schneller & mehr Storage
```