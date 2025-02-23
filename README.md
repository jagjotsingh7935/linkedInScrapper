# LinkedIn Job Clone

This project is a LinkedIn Job Clone with a Django backend and a React (Vite) frontend.

## Prerequisites

Ensure you have the following installed:
- **Python 3.9** (for the backend)
- **npm** (for the frontend)
- **Virtual Environment (venv)** (recommended for Python projects)

## Project Structure
```
linkedinjob/
│── job/                # Django Backend
│── jobFrontend/        # React Frontend (Vite)
```

---

## Backend Setup (Django)

1. **Navigate to the backend directory:**
   ```bash
   cd job
   ```

2. **Create and activate a virtual environment:**
   - On Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - On MacOS/Linux:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   The backend will run on `http://127.0.0.1:8000`

---

## Frontend Setup (React with Vite)

1. **Navigate to the frontend directory:**
   ```bash
   cd ../jobFrontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:3000`

---

## Additional Information

- Ensure the backend is running before starting the frontend to avoid API errors.
- Update the API base URL in the frontend if necessary to match the backend server address.
- Use `.env` files to manage environment variables if needed.

---

## Author
Jagjot Singh
