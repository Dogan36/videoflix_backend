# Videoflix Backend Repository

**Videoflix Backend** is the server-side component of the Videoflix full‑stack streaming application, developed as part of the Full‑Stack training at Developer Academy. It provides RESTful APIs for movies, user authentication, streaming, progress tracking, and asynchronous video processing tasks.

## Features

- **User Management**: Registration, email verification, login (Token authentication), password reset.
- **Movie Catalog**: CRUD views for movies, categories, and progress entries.
- **Video Streaming**: Range‑request support for efficient streaming at multiple resolutions.
- **Progress Tracking**: Endpoints to record and retrieve playback progress and completion status.
- **Asynchronous Processing**: RQ‑based tasks to convert videos into multiple resolutions, generate thumbnails, extract trailers, and compute durations automatically upon upload.
- **Role‑based Access**: Authenticated endpoints with permissions for public or protected resources.
- **Pagination & Filtering**: Home endpoints and "load more" APIs support page sizes based on client needs.
- **Comprehensive Testing**: Unit tests for models, serializers, views, tasks, signals, and utilities (achieving over 80% coverage recommended).

## Directory Structure

```
backend/
├── movies/            # App: models, serializers, views, tasks, signals, utilities, pagination
├── users/             # App: custom user model, serializers, views, email utils
├── media/             # Stored media files (videos, thumbnails, trailers)
├── settings.py        # Django settings, installed apps, middleware, RQ config
├── urls.py            # URL routing for API endpoints
├── tests/             # Unit tests for both apps
└── README.md          # This file
```

## Setup & Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/your-org/videoflix-backend.git
   cd videoflix-backend
   ```
2. **Create a virtual environment & install dependencies:**
   ```bash
   python -m venv env
   source env/bin/activate   # on Windows: env\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure environment variables** in `.env` (e.g. SECRET_KEY, DATABASE_URL, FRONTEND_URL).
4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```
5. **Start RQ worker:**
   ```bash
   rq worker default
   ```
6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## Testing

- **Unit tests:**
  ```bash
  python manage.py test
  ```
- **Coverage (optional using coverage.py):**
  ```bash
  coverage run --source='.' manage.py test
  coverage report
  ```

📄 License
MIT License
Copyright (c) 2025 Dogan Celik

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
---

*This project was developed as part of the Full‑Stack training program at Developer Academy.*

