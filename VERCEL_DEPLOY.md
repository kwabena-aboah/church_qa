# Deploying to Vercel

## Project setup

Import this repository into Vercel with the repository root as the project root. Vercel detects the root `manage.py`, uses `church_qa.wsgi.application`, installs dependencies from `requirements.txt`, and collects Django static files automatically. No custom build command or `api/` wrapper is needed.

The project pins Python 3.12 in `.python-version`. `vercel.json` sets a 60-second function limit for the Django WSGI entry point.

## Environment variables

Set these in Vercel Project Settings for every environment that should run the app:

- `SECRET_KEY`: generate a unique value with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`.
- `DEBUG`: `False` for production and preview deployments.
- `DATABASE_URL`: a persistent PostgreSQL connection URL. The app intentionally refuses to use local SQLite on Vercel because function filesystems are not persistent.
- `ALLOWED_HOSTS`: comma-separated custom domains, without schemes. Vercel deployment and project hostnames are added automatically.
- `CSRF_TRUSTED_ORIGINS`: comma-separated HTTPS origins, including the production custom domain, for example `https://sermons.example.com`.
- `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_VERIFY_TOKEN` if WhatsApp delivery and webhook verification are enabled.

Vercel provides `VERCEL_URL`, `VERCEL_BRANCH_URL`, and `VERCEL_PROJECT_PRODUCTION_URL`; Django adds those hostnames to `ALLOWED_HOSTS` and their HTTPS origins to `CSRF_TRUSTED_ORIGINS`. The custom domain still needs to be listed in `CSRF_TRUSTED_ORIGINS`.

Apply database migrations to the configured PostgreSQL database before relying on the deployment. Do not use the project’s local `db.sqlite3` for production data.

## Runtime limitations

Vercel serves collected static assets from its CDN. Uploaded speaker photos and sermon thumbnails are stored under `MEDIA_ROOT` in the current app, but Vercel function filesystems are ephemeral; configure an S3-compatible object store such as Cloudflare R2 before relying on uploads. Cloudflare API credentials alone do not provide Django media storage.

Vercel does not run a persistent Celery worker. Without an independently hosted broker and worker, question delivery runs synchronously through the app’s existing fallback path. Keep external API timeouts within the function duration limit.
