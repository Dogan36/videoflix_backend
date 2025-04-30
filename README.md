# Backend Repository

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

# Frontend Repository

**Videoflix Frontend** is the client‑side React application that consumes the Videoflix Backend APIs, built as part of the Full‑Stack training at Developer Academy. It provides a modern UI for browsing, streaming, and tracking movie progress.

## Features

- **Responsive Design**: Mobile‑friendly layout, adaptive video player controls, auto‑hide header.
- **Custom Video Player**: Play/Pause, volume slider, resolution switcher, fullscreen, progress bar with seek.
- **Dynamic Data Fetching**: Axios/fetch wrappers for JSON and binary (video) data, with authentication tokens.
- **Infinite Scrolling**: IntersectionObserver‑based loading of additional movies per category.
- **Authentication Flows**: Login, signup, password reset, activation, and protected routes.
- **Global Toast Notifications**: Context‑based toast provider for success/error messages.
- **Code Splitting & Routing**: React Router for pages (Home, Watch, Login, Activation, Reset Password).

## Directory Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components (VideoPlayer, Toast, Header, Cards)
│   ├── pages/          # Top‑level pages (Home, Watch, Login, Activation, Reset)
│   ├── services/       # API wrappers (getData, postData) & auth helpers
│   ├── contexts/       # React Contexts (ToastProvider, Auth)
│   ├── utils/          # Helpers (form validation, column count)
│   ├── assets/         # Images, icons, styles
│   ├── App.jsx         # App component with routes
│   └── index.jsx       # App bootstrap (ToastProvider, ReactDOM.render)
├── public/             # Static files (favicon, index.html)
├── .env                # Environment variables (REACT_APP_API_URL)
├── package.json        # NPM scripts and dependencies
└── README.md           # This file
```

## Setup & Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/your-org/videoflix-frontend.git
   cd videoflix-frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Configure environment variables** in `.env` (e.g. `REACT_APP_API_URL=http://localhost:8000/`).
4. **Start the dev server:**
   ```bash
   npm run dev
   ```
5. **Build for production:**
   ```bash
   npm run build
   ```

## Testing

- **Run unit tests:**
  ```bash
  npm test
  ```
- **(Optional) Coverage with Jest:**
  ```bash
  npm test -- --coverage
  ```

📄 License
MIT © Dogan Celik
---

*This project was developed as part of the Full‑Stack training program at Developer Academy.*

