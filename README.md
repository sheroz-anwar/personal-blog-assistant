# Personal Blog Assistant - FastAPI Application

A modern, high-performance blog application built with FastAPI for creating, managing, and serving blog posts with comprehensive API endpoints.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

Personal Blog Assistant is a FastAPI-based REST API application designed for managing blog posts and related content. It provides a robust backend for blog operations with automatic API documentation, async support, and production-ready features.

## Features

✨ **Core Features:**
- RESTful API for blog post management
- Async/await support for high performance
- Automatic OpenAPI (Swagger) documentation
- Input validation with Pydantic models
- Error handling and status codes
- Pagination support
- Search and filter capabilities
- User authentication ready architecture

🔧 **Developer Features:**
- Interactive API documentation (Swagger UI)
- Hot reload development server
- Comprehensive logging
- Type hints throughout codebase
- Easy deployment configuration

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Python package manager (comes with Python)
- **Git** - Version control system
- **Virtual Environment** - Recommended for dependency isolation

### System Requirements

- **OS:** Linux, macOS, or Windows
- **RAM:** Minimum 512MB (1GB recommended)
- **Disk Space:** 500MB for development environment

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/sheroz-anwar/personal-blog-assistant.git
cd personal-blog-assistant
```

### Step 2: Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
pip list
python -c "import fastapi; print(f'FastAPI {fastapi.__version__} installed successfully')"
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Application Configuration
APP_NAME=Personal Blog Assistant
APP_VERSION=1.0.0
DEBUG=True

# Server Configuration
HOST=127.0.0.1
PORT=8000
RELOAD=True

# Database Configuration (if using)
DATABASE_URL=sqlite:///./blog.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
```

### Loading Environment Variables

The application automatically loads `.env` file using `python-dotenv` if installed:

```bash
pip install python-dotenv
```

## Running the Application

### Development Server

```bash
fastapi dev main.py
```

Or using Uvicorn directly:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Production Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the Application

- **API Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

## API Documentation

The API documentation is automatically generated and available through two interfaces:

### Swagger UI (Interactive)
Navigate to `http://localhost:8000/docs` to access the interactive Swagger UI where you can:
- View all endpoints
- See request/response schemas
- Test endpoints directly from the browser

### ReDoc (Read-Only)
Navigate to `http://localhost:8000/redoc` for a clean, read-only documentation view.

## API Endpoints

### Blog Posts

#### Get All Posts
```
GET /api/posts
```

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Number of records to return (default: 10)
- `search` (str, optional): Search term for post title or content

**Response:**
```json
{
  "total": 15,
  "items": [
    {
      "id": 1,
      "title": "My First Blog Post",
      "slug": "my-first-blog-post",
      "content": "Blog content here...",
      "excerpt": "Short excerpt...",
      "author": "John Doe",
      "created_at": "2025-12-28T10:00:00Z",
      "updated_at": "2025-12-28T10:00:00Z",
      "tags": ["python", "fastapi"],
      "published": true
    }
  ]
}
```

#### Get Single Post
```
GET /api/posts/{post_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "My First Blog Post",
  "slug": "my-first-blog-post",
  "content": "Blog content here...",
  "excerpt": "Short excerpt...",
  "author": "John Doe",
  "created_at": "2025-12-28T10:00:00Z",
  "updated_at": "2025-12-28T10:00:00Z",
  "tags": ["python", "fastapi"],
  "published": true,
  "views": 42
}
```

#### Create Post
```
POST /api/posts
```

**Request Body:**
```json
{
  "title": "My Blog Post",
  "slug": "my-blog-post",
  "content": "Full blog content...",
  "excerpt": "Short summary...",
  "author": "Your Name",
  "tags": ["python", "webdev"],
  "published": true
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "title": "My Blog Post",
  "slug": "my-blog-post",
  "content": "Full blog content...",
  "excerpt": "Short summary...",
  "author": "Your Name",
  "created_at": "2025-12-28T14:26:11Z",
  "updated_at": "2025-12-28T14:26:11Z",
  "tags": ["python", "webdev"],
  "published": true
}
```

#### Update Post
```
PUT /api/posts/{post_id}
```

**Request Body:** (Same as Create Post)

**Response:** 200 OK

#### Delete Post
```
DELETE /api/posts/{post_id}
```

**Response:** 204 No Content

#### Get Posts by Tag
```
GET /api/posts/tags/{tag}
```

**Response:** Array of posts with the specified tag

#### Get Posts by Author
```
GET /api/posts/author/{author_name}
```

**Response:** Array of posts by the specified author

### Health Check

#### Health Status
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-28T14:26:11Z",
  "version": "1.0.0"
}
```

## Usage Examples

### Using cURL

**Get all posts:**
```bash
curl http://localhost:8000/api/posts
```

**Get posts with pagination:**
```bash
curl "http://localhost:8000/api/posts?skip=0&limit=5"
```

**Search posts:**
```bash
curl "http://localhost:8000/api/posts?search=python"
```

**Create a new post:**
```bash
curl -X POST http://localhost:8000/api/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI Tips",
    "slug": "fastapi-tips",
    "content": "Here are some useful FastAPI tips...",
    "excerpt": "FastAPI best practices",
    "author": "Jane Doe",
    "tags": ["fastapi", "python"],
    "published": true
  }'
```

**Update a post:**
```bash
curl -X PUT http://localhost:8000/api/posts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "slug": "fastapi-tips",
    "content": "Updated content...",
    "excerpt": "FastAPI best practices",
    "author": "Jane Doe",
    "tags": ["fastapi", "python"],
    "published": true
  }'
```

**Delete a post:**
```bash
curl -X DELETE http://localhost:8000/api/posts/1
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Get all posts
response = requests.get(f"{BASE_URL}/api/posts")
posts = response.json()
print(posts)

# Create a post
new_post = {
    "title": "Python FastAPI",
    "slug": "python-fastapi",
    "content": "A comprehensive guide to FastAPI...",
    "excerpt": "Learn FastAPI",
    "author": "John Developer",
    "tags": ["python", "fastapi", "web"],
    "published": True
}
response = requests.post(f"{BASE_URL}/api/posts", json=new_post)
created_post = response.json()
print(f"Created post with ID: {created_post['id']}")

# Get single post
response = requests.get(f"{BASE_URL}/api/posts/1")
post = response.json()
print(post)

# Update a post
updated_post = {...}
response = requests.put(f"{BASE_URL}/api/posts/1", json=updated_post)
print(response.status_code)

# Delete a post
response = requests.delete(f"{BASE_URL}/api/posts/1")
print(f"Deleted: {response.status_code == 204}")
```

### Using JavaScript/Fetch API

```javascript
const BASE_URL = "http://localhost:8000";

// Get all posts
async function getAllPosts() {
  const response = await fetch(`${BASE_URL}/api/posts`);
  return await response.json();
}

// Create a post
async function createPost(postData) {
  const response = await fetch(`${BASE_URL}/api/posts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(postData),
  });
  return await response.json();
}

// Get single post
async function getPost(postId) {
  const response = await fetch(`${BASE_URL}/api/posts/${postId}`);
  return await response.json();
}

// Update a post
async function updatePost(postId, postData) {
  const response = await fetch(`${BASE_URL}/api/posts/${postId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(postData),
  });
  return await response.json();
}

// Delete a post
async function deletePost(postId) {
  const response = await fetch(`${BASE_URL}/api/posts/${postId}`, {
    method: "DELETE",
  });
  return response.status === 204;
}

// Usage
(async () => {
  const allPosts = await getAllPosts();
  console.log(allPosts);
})();
```

## Development

### Project Structure

```
personal-blog-assistant/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in repo)
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore rules
├── app/
│   ├── __init__.py
│   ├── models/            # Data models
│   │   └── post.py
│   ├── routes/            # API routes
│   │   └── posts.py
│   ├── schemas/           # Pydantic schemas
│   │   └── post.py
│   ├── services/          # Business logic
│   │   └── post_service.py
│   └── database.py        # Database configuration
├── tests/                 # Test files
│   ├── test_posts.py
│   └── conftest.py
└── README.md              # This file
```

### Code Style

The project follows PEP 8 style guidelines. Use the following tools for code quality:

```bash
# Install development tools
pip install black flake8 isort pylint

# Format code
black app/ main.py

# Check style
flake8 app/ main.py

# Sort imports
isort app/ main.py

# Lint code
pylint app/ main.py
```

## Testing

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_posts.py

# Run with verbose output
pytest -v

# Run tests in watch mode
pytest-watch
```

### Example Test File

```python
# tests/test_posts.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_all_posts():
    response = client.get("/api/posts")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_create_post():
    post_data = {
        "title": "Test Post",
        "slug": "test-post",
        "content": "Test content",
        "excerpt": "Test excerpt",
        "author": "Tester",
        "tags": ["test"],
        "published": True
    }
    response = client.post("/api/posts", json=post_data)
    assert response.status_code == 201
    assert response.json()["title"] == "Test Post"
```

## Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t personal-blog-assistant .
docker run -p 8000:8000 personal-blog-assistant
```

### Deployment Platforms

#### Heroku
```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create your-app-name

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main
```

#### PythonAnywhere
1. Upload your code
2. Create a web app with Python 3.8+
3. Configure WSGI with FastAPI app
4. Set environment variables
5. Reload the web app

#### AWS (EC2/Elastic Beanstalk)
```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 personal-blog-assistant

# Create environment
eb create production

# Deploy
eb deploy
```

## Troubleshooting

### Common Issues

**Issue: ModuleNotFoundError: No module named 'fastapi'**

Solution:
```bash
pip install -r requirements.txt
# Or specifically
pip install fastapi uvicorn
```

**Issue: Port 8000 already in use**

Solution:
```bash
# Use a different port
uvicorn main:app --port 8001

# Or kill the process using port 8000
# On macOS/Linux:
lsof -i :8000
kill -9 <PID>

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Issue: Database connection errors**

Solution:
- Check DATABASE_URL in `.env`
- Verify database file/server is accessible
- Check database permissions
- Run migrations if needed

**Issue: Async warnings or event loop errors**

Solution:
```bash
pip install --upgrade uvicorn
# Ensure using uvicorn >= 0.20.0
```

**Issue: Slow performance in development**

Solution:
- Disable debug mode in production
- Use `--workers` parameter
- Check database queries with logging
- Enable caching where appropriate

### Getting Help

- Check FastAPI documentation: https://fastapi.tiangolo.com
- Review Uvicorn docs: https://www.uvicorn.org
- Search existing GitHub issues
- Create a new issue with detailed information

## Performance Optimization

### Tips for Better Performance

1. **Use Database Indexes:**
   - Index frequently searched fields
   - Index foreign keys

2. **Enable Caching:**
   ```python
   from fastapi_cache2 import FastAPICache2
   from fastapi_cache2.backends.redis import RedisBackend
   ```

3. **Use Connection Pooling:**
   - Configure database connection pools
   - Use SQLAlchemy session pooling

4. **Async Operations:**
   - Use async database drivers
   - Keep blocking operations minimal

5. **Load Balancing:**
   - Run multiple workers
   - Use reverse proxy (nginx)

## Security Best Practices

- ✅ Use HTTPS in production
- ✅ Validate all inputs with Pydantic
- ✅ Use environment variables for secrets
- ✅ Implement authentication/authorization
- ✅ Add rate limiting
- ✅ Use CORS properly
- ✅ Keep dependencies updated
- ✅ Run security audits regularly

```bash
# Check for vulnerable dependencies
pip install safety
safety check
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Write/update tests
4. Run tests to ensure they pass
5. Format code with `black`
6. Check with `flake8`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
- Open an issue on GitHub
- Email: your-email@example.com
- Documentation: https://fastapi.tiangolo.com

## Changelog

### Version 1.0.0 (2025-12-28)
- Initial release
- Basic CRUD operations for blog posts
- API documentation with Swagger/ReDoc
- Full async support
- Comprehensive error handling

---

**Made with ❤️ by [sheroz-anwar](https://github.com/sheroz-anwar)**

Last Updated: 2025-12-28
