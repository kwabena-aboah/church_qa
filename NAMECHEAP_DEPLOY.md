# Deploying to Namecheap Shared Hosting

## Prerequisites
- Namecheap shared hosting with cPanel
- Python 3.11+ available via cPanel or SSH
- SSH access enabled

## Steps

### 1. Set up Python App in cPanel
- cPanel > Setup Python App
- Python version: 3.11
- Application root: church_qa
- Application URL: your domain or subdirectory
- Click CREATE

### 2. Upload your code
Upload via FTP (FileZilla) or cPanel File Manager.
Recommended path: /home/username/church_qa/

### 3. Install dependencies (via SSH)
```bash
cd ~/church_qa
source /home/username/virtualenv/church_qa/3.11/bin/activate
pip install -r requirements.txt
```

### 4. Create .env file
```bash
cp .env.example .env
nano .env   # fill in your values
```

### 5. Run migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 6. Configure passenger_wsgi.py (cPanel Python Apps)
cPanel creates this automatically. Verify it points to church_qa.wsgi.

### 7. Configure .htaccess (in public_html or app root)
```apache
RewriteEngine On
RewriteRule ^(.*)$ /church_qa/passenger_wsgi.py/$1 [QSA,L]
```

### 8. SQLite vs MySQL
For Namecheap shared, SQLite works fine for small churches (<10k questions).
For MySQL, update settings.py DATABASE section and install mysqlclient.

### Important Notes
- Celery workers are NOT available on shared hosting.
- Questions will be sent synchronously (slight delay on submission).
- For async sending, upgrade to Namecheap VPS or use Render.com.
- Redis is not available on shared hosting.

### Namecheap VPS (recommended for Celery)
If on VPS, run:
```bash
sudo apt install redis-server
celery -A church_qa worker --detach --loglevel=info
```
