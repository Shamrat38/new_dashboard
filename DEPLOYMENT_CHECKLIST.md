# Django Server Deployment Checklist

## Quick Fix for 500 Errors

### 1. Immediate Steps (Run on Server)

```bash
# 1. Install python-dotenv
pip install python-dotenv

# 2. Create .env file with production settings
cp env_example.txt .env
# Edit .env file with your production values

# 3. Set DEBUG=False
echo "DEBUG=False" >> .env

# 4. Run migrations
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Create media directory
mkdir -p media

# 7. Set proper permissions
chmod 755 staticfiles
chmod 755 media
chmod 755 logs

# 8. Run the debug script
python debug_server.py
```

### 2. Environment Variables (.env file)

Create a `.env` file in your project root with:

```env
SECRET_KEY=your-new-secret-key-here
DEBUG=False
DB_NAME=newdashboard_db
DB_USER=neworangepi_user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Common 500 Error Causes & Solutions

#### Database Issues
- **Problem**: Database connection failed
- **Solution**: Check database credentials and ensure PostgreSQL is running
- **Check**: `python manage.py dbshell`

#### Missing Migrations
- **Problem**: Database schema not up to date
- **Solution**: `python manage.py migrate`

#### Static Files Issues
- **Problem**: Static files not found
- **Solution**: `python manage.py collectstatic --noinput`

#### Import Errors
- **Problem**: Missing dependencies
- **Solution**: `pip install -r requirements.txt`

#### Permission Issues
- **Problem**: File/directory permissions
- **Solution**: 
  ```bash
  chmod 755 staticfiles
  chmod 755 media
  chmod 755 logs
  ```

### 4. Server Configuration

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/your/project/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Gunicorn Configuration
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn --bind 0.0.0.0:8000 main.wsgi:application
```

### 5. Debugging Steps

1. **Check Django Logs**:
   ```bash
   tail -f logs/django_errors.log
   ```

2. **Check Server Logs**:
   ```bash
   # Nginx
   tail -f /var/log/nginx/error.log
   
   # Apache
   tail -f /var/log/apache2/error.log
   ```

3. **Test Database Connection**:
   ```bash
   python manage.py dbshell
   ```

4. **Test Static Files**:
   ```bash
   python manage.py findstatic admin/css/base.css
   ```

5. **Run Debug Script**:
   ```bash
   python debug_server.py
   ```

### 6. Production Security Checklist

- [ ] DEBUG=False
- [ ] SECRET_KEY is secure and not in version control
- [ ] Database credentials in environment variables
- [ ] ALLOWED_HOSTS configured properly
- [ ] Static files served by web server (nginx/apache)
- [ ] HTTPS enabled
- [ ] Security headers configured

### 7. Quick Test Commands

```bash
# Test Django setup
python manage.py check

# Test database
python manage.py check --database default

# Test static files
python manage.py collectstatic --dry-run

# Run development server (for testing)
python manage.py runserver 0.0.0.0:8000
```

## Emergency Rollback

If you need to quickly rollback:

1. Set DEBUG=True temporarily
2. Check logs for specific errors
3. Fix the issue
4. Set DEBUG=False again

```bash
echo "DEBUG=True" > .env
# Fix the issue
echo "DEBUG=False" > .env
```
