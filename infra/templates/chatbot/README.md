# Backend API

This project implements a backend API using Django, Django REST Framework, and PostgreSQL.

## Project Structure

The project structure is as follows:

```
backend/
├── manage.py
├── project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   └── bot/
│       ├── __init__.py
│       ├── views.py
│       └── urls.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your database settings in `project/settings.py`. Environment variables are used for PostgreSQL configuration:
   - POSTGRES_DB
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - POSTGRES_HOST (default: localhost)
   - POSTGRES_PORT (default: 5432)
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API

The API is built using Django REST Framework. Additional endpoints can be added under `apps/api/`.

## Additional Notes

- Adjust the SECRET_KEY in `project/settings.py` for production.
- Debug mode is enabled by default; change it as needed.
- Extend the project structure by adding more apps or configurations as your project grows.