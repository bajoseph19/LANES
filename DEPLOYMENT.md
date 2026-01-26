# LANES Deployment Guide

## Quick Start (Development)

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Download NLTK Data**
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

3. **Initialize Database**
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

4. **Run the Application**
```bash
# Development mode (with debug)
export FLASK_DEBUG=true
python app.py

# Production mode (without debug)
export FLASK_DEBUG=false
python app.py
```

The application will be available at `http://localhost:5000`

## Production Deployment

### Environment Variables

Set these environment variables for production:

```bash
export SECRET_KEY="your-secret-key-here"  # Generate a strong random key
export FLASK_DEBUG=false  # Always false in production
export DATABASE_URL="sqlite:///production.db"  # Or use PostgreSQL
```

### Using Gunicorn (Recommended)

1. **Install Gunicorn**
```bash
pip install gunicorn
```

2. **Run with Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

1. **Create Dockerfile**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

COPY . .

RUN python -c "from app import app, db; app.app_context().push(); db.create_all()"

ENV FLASK_DEBUG=false

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

2. **Build and Run**
```bash
docker build -t lanes-app .
docker run -p 5000:5000 -e SECRET_KEY="your-secret-key" lanes-app
```

### Database Migration (Production)

For production, consider using PostgreSQL instead of SQLite:

1. **Install PostgreSQL Driver**
```bash
pip install psycopg2-binary
```

2. **Update Database URI**
```python
# In app.py
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lanes.db')
```

3. **Set Environment Variable**
```bash
export DATABASE_URL="postgresql://user:password@localhost/lanes"
```

### Security Checklist

- [ ] Set a strong `SECRET_KEY` environment variable
- [ ] Set `FLASK_DEBUG=false` in production
- [ ] Use HTTPS (configure reverse proxy like Nginx)
- [ ] Keep dependencies updated (`pip list --outdated`)
- [ ] Regular database backups
- [ ] Rate limiting on signup/login endpoints (consider Flask-Limiter)
- [ ] Monitor application logs

### Nginx Configuration (Optional)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Monitoring and Logs

Monitor these aspects in production:

1. **Application Logs**: Check Flask logs for errors
2. **Database Size**: Monitor SQLite file size
3. **Response Times**: Track API endpoint performance
4. **Failed Parsing Attempts**: Monitor parser success rate

### Scaling Considerations

- Use PostgreSQL for better concurrent access
- Implement caching for frequently accessed recipes
- Consider background job queue (Celery) for parsing
- Use CDN for static assets
- Implement database connection pooling

## Testing

Run the test suite before deployment:

```bash
python test_app.py
python test_parser.py
```

All tests should pass before deploying to production.

## Troubleshooting

### Issue: Database locked errors
**Solution**: Switch from SQLite to PostgreSQL for production

### Issue: Parser not finding ingredients
**Solution**: Check that `food_words_.csv` and `coll_words_.csv` files exist

### Issue: NLTK errors
**Solution**: Run `python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"`

### Issue: Memory usage high
**Solution**: Limit concurrent workers in Gunicorn, use smaller NLTK datasets
