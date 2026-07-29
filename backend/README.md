# Akkerman Backend API

A stateless Flask application providing HTTP API endpoints with SQLAlchemy database integration.

## Features

- **Flask Framework**: Lightweight, production-ready Python web framework
- **SQLAlchemy ORM**: Object-relational mapping with connection pooling
- **Configurable Database**: SQLite by default, supports PostgreSQL, MySQL, etc.
- **Health Endpoint**: `/healthz` returns 200 if application and database are healthy
- **Connection Pooling**: Best practices implementation with verification and recycling
- **Environment Configuration**: Fully configurable via environment variables
- **Docker Ready**: Production Dockerfile with Gunicorn WSGI server
- **Comprehensive Tests**: Unit tests for all endpoints and configuration

## Quick Start

### Local Development

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env if needed (defaults to SQLite)
```

3. **Run the application**:
```bash
python app.py
```

4. **Test the health endpoint**:
```bash
curl http://localhost:5000/healthz
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Docker

1. **Build the image**:
```bash
docker build -t akkerman-backend:0.1.0 .
```

2. **Run the container**:
```bash
docker run -p 5000:5000 akkerman-backend:0.1.0
```

3. **Test from outside the container**:
```bash
curl http://localhost:5000/healthz
```

## API Endpoints

### Health Check
```
GET /healthz
```
- **Status Codes**: 
  - `200 OK` - Application and database are healthy
  - `503 Service Unavailable` - Database connection failed
- **Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Status
```
GET /api/v1/status
```
- **Status Code**: `200 OK`
- **Response**:
```json
{
  "version": "0.1.0",
  "status": "running",
  "service": "akkerman-backend"
}
```

## Configuration

### Environment Variables

#### Database Configuration
- `DATABASE_URL`: Full database connection string (overrides SQLALCHEMY_DATABASE_URI)
- `SQLALCHEMY_DATABASE_URI`: Alternative to DATABASE_URL (default: `sqlite:///./akkerman.db`)

#### Connection Pool Settings
- `DB_POOL_SIZE`: Number of connections to maintain (default: `5`)
- `DB_MAX_OVERFLOW`: Additional connections allowed (default: `10`)
- `SQLALCHEMY_ECHO`: Log SQL queries (default: `False`)

#### Flask Settings
- `FLASK_ENV`: Environment mode - `development`, `testing`, or `production` (default: `development`)
- `FLASK_APP`: Application module (default: `app.py`)
- `FLASK_DEBUG`: Enable debug mode (default: `False`)

### Database Examples

**SQLite (default)**:
```
SQLALCHEMY_DATABASE_URI=sqlite:///./akkerman.db
```

**PostgreSQL**:
```
DATABASE_URL=postgresql://user:password@localhost:5432/akkerman
```

**MySQL**:
```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/akkerman
```

## Testing

Run the test suite:
```bash
cd backend
pip install pytest
pytest test_app.py -v
```

## Architecture

### Connection Pooling Best Practices

This application implements SQLAlchemy connection pooling with these optimizations:

1. **Pool Pre-Ping** (`pool_pre_ping=True`)
   - Verifies each connection before use
   - Prevents "lost connection" errors from database restarts
   - Minimal performance impact

2. **Connection Recycling** (`pool_recycle=3600`)
   - Recycles connections after 1 hour
   - Prevents stale connections from being used
   - Important for databases with idle connection timeouts (e.g., MySQL 8-hour default)

3. **Pool Size Configuration** (`pool_size=5`, `max_overflow=10`)
   - Maintains 5 persistent connections
   - Allows up to 10 additional temporary connections
   - Configurable via environment variables for different deployment scenarios

4. **Synchronous Thread-based Model**
   - Uses Flask's synchronous request handling
   - One database connection per request
   - Suitable for I/O-bound operations with moderate concurrency
   - Can be upgraded to async (FastAPI) for higher concurrency requirements

### Application Structure

```
backend/
├── app.py                 # Flask application factory and routes
├── database.py            # SQLAlchemy initialization and models
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── test_app.py            # Unit tests
├── Dockerfile             # Production Docker image
└── .env.example           # Environment variable template
```

## Deployment

### Production Considerations

1. **WSGI Server**: Use Gunicorn (included in requirements.txt)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

2. **Database**: Use PostgreSQL or MySQL in production (not SQLite)
```bash
DATABASE_URL=postgresql://user:pass@host:5432/akkerman
```

3. **Connection Pool**: Adjust based on deployment:
   - Cloud Functions: `pool_size=1, max_overflow=5`
   - Container (4 CPU): `pool_size=5, max_overflow=10`
   - VM (8 CPU): `pool_size=10, max_overflow=20`

4. **Health Checks**: Container orchestration (Kubernetes, Docker Swarm) can use `/healthz` endpoint

## Development

### Adding New Endpoints

1. Define your route in `app.py`:
```python
@app.route('/api/v1/users', methods=['GET'])
def get_users():
    return jsonify({"users": []}), 200
```

2. Add corresponding tests in `test_app.py`

3. Run tests to verify

### Adding Database Models

1. Create model in `database.py`:
```python
class User(BaseModel):
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
```

2. Models are automatically created when app starts (see `init_db()`)

## Troubleshooting

### Connection Pool Issues
- Check `pool_recycle` timeout matches your database's idle timeout
- Monitor connection count: `DB_POOL_SIZE + DB_MAX_OVERFLOW`
- Enable `SQLALCHEMY_ECHO=True` to see SQL queries

### Database Not Connecting
- Verify `DATABASE_URL` or `SQLALCHEMY_DATABASE_URI` is correct
- Check database credentials and network connectivity
- Review application logs for specific error messages

## License

See LICENSE.md in the project root.
