# Flask-Firestore JWT Authentication with Refresh Token Rotation

This project demonstrates a secure, production-ready authentication mechanism using **JSON Web Tokens (JWTs)** in a **Flask** application. It implements the common **Access Token** and **Refresh Token** strategy, storing user data in **Google Firestore**.

This architecture prioritizes security by using a short-lived Access Token stored in a server-side session and a long-lived Refresh Token stored in a secure, HTTP-only cookie to handle silent re-authentication.

## Features

- **Dual Token Strategy:** Uses a short-lived **Access Token** (5 minutes) for API access and a long-lived **Refresh Token** (30 days) for seamless re-authentication.
- **Token Storage Security:**
  - **Access Token:** Stored in the server-side **Flask Session** to prevent client-side JavaScript access (XSS mitigation).
  - **Refresh Token:** Stored in an **HTTP-only cookie** for enhanced security.
- **Silent Refresh:** The `/refresh` endpoint automatically exchanges an expired Access Token for a new one using the valid Refresh Token, providing a smooth user experience.
- **User Registration & Login:** Utilizes **Google Firestore** as the persistence layer for user credentials.
  - ⚠️ **Security Note:** The provided code saves passwords in plaintext for demonstration purposes. **In a real application, you must HASH passwords** (e.g., using bcrypt) before saving them and compare against the hash during login.
- **Technology Stack:** Flask, PyJWT, Python `secrets`, Google Firestore Admin SDK.

## Project Structure

. ├── app.py ├── firestore_utils.py ├── .env <-- IMPORTANT: This file is ignored by Git and holds secrets! ├── venv/ <-- IMPORTANT: This folder is ignored by Git and holds the virtual environment. ├── templates/ │ ├── dashboard.html │ ├── index.html │ └── register.html └── static/ ├── css/ │ └── style.css └── js/ └── script.js

## Setup and Installation

### 1. Prerequisites

- A Google Cloud Project with **Firestore Database** enabled.

### 2. Get the Code

```bash
git clone https://github.com/jpandya1161/Flask-Firestore-JWT-Authentication-with-Refresh-Token-Rotation.git
cd flask-firestore-jwt-auth
```

### 3. Environment Variables (.env)

- This project is configured to load its sensitive credentials from environment variables using the python-dotenv library. Create a file named .env in the root directory and populate it with your Firestore Service Account details.

### 4. Run the Application

[cite_start]The application initializes Firestore on startup.

```bash
python app.py
```
