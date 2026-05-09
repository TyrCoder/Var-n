# Varon E-Commerce Platform - Deployment Guide

## Quick Start for Render

### Prerequisites
- GitHub account
- Render account (free at render.com)
- Supabase PostgreSQL database credentials

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Varon e-commerce platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/varon-ecommerce.git
git push -u origin main
```

### Step 2: Deploy to Render

1. Go to **render.com** → Sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select this repository
4. Fill in deployment details:
   - **Name**: `varon-ecommerce`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Under **Environment**, add these variables:
   ```
   DB_HOST=db.pzmyfchyzowlkufqabva.supabase.co
   DB_USER=postgres
   DB_PASSWORD=@Varon5Memb
   DB_NAME=postgres
   DB_PORT=5432
   SECRET_KEY=your-secret-key-change-in-production-please
   SESSION_COOKIE_SECURE=true
   FLASK_ENV=production
   ```
6. Click **"Create Web Service"**
7. Wait for deployment (takes 2-3 minutes)

### Environment Variables

Create a `.env` file locally (not committed to git):

```env
# Database Configuration (PostgreSQL)
DB_HOST=db.pzmyfchyzowlkufqabva.supabase.co
DB_USER=postgres
DB_PASSWORD=@Varon5Memb
DB_NAME=postgres
DB_PORT=5432

# Flask Secret Key
SECRET_KEY=your-secret-key-change-in-production-please

# Email Configuration (for OTP via Email)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=sedocode7@gmail.com
MAIL_PASSWORD=fgnuvbxxmzxworix
MAIL_DEFAULT_SENDER=Varón Apparel <noreply@varon.com>

# Session Security
SESSION_COOKIE_SECURE=false  # Set to true in production with HTTPS
```

### Files Included

- **Procfile**: Tells Render how to run the app
- **runtime.txt**: Specifies Python version
- **requirements.txt**: All Python dependencies
- **.gitignore**: Prevents sensitive files from being committed

### Troubleshooting

**Cold start takes too long?**
- This is normal for free tier. Upgrade to "Standard" plan ($7/month) for faster boots.

**Database connection failed?**
- Check environment variables in Render dashboard match your `.env`
- Verify Supabase credentials are correct
- Test locally first: `python -c "import psycopg2; print('OK')"`

**App crashes after deploy?**
- Check Render logs (Dashboard → Your App → Logs)
- Common issue: Missing PostgreSQL compatibility in SQL queries (see notes below)

### PostgreSQL Migration Notes

This app was originally MySQL-based. Key changes made:

1. **Driver**: `mysql-connector-python` → `psycopg2`
2. **SHOW COLUMNS**: Changed to use PostgreSQL information schema
3. **Data types**: Some MySQL-specific types may need adjustment
4. **AUTO_INCREMENT**: Changed to SERIAL in PostgreSQL

If you encounter SQL errors in production:
- Check the error message in Render logs
- Modify the problematic SQL in `app.py`
- Commit and push - Render auto-redeploys

### Performance Tips

- **Use connection pooling** for high traffic (pgBouncer)
- **Enable caching** for PSGC API responses
- **Monitor database queries** on Supabase dashboard
- **Set up CDN** for static assets (Cloudflare, etc.)

### Custom Domain

1. In Render dashboard: **Settings** → **Custom Domain**
2. Add your domain (e.g., varon.com)
3. Follow DNS setup instructions
4. Free SSL certificate automatically applied

### Support

For Render issues: https://render.com/docs
For PostgreSQL issues: https://www.postgresql.org/docs/
For Flask issues: https://flask.palletsprojects.com/

---

**Happy deploying! 🚀**
