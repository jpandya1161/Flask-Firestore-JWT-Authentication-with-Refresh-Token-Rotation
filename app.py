import secrets
from datetime import datetime, timedelta, timezone
import jwt
import os
from dotenv import load_dotenv
# IMPORTANT: Import the new register_new_user function
from firestore_utils import verify_user_credentials, initialize_firestore, register_new_user
from flask import Flask, jsonify, request, session, redirect, url_for, render_template 

# --- NEW: Load environment variables from .env file FIRST ---
load_dotenv() 
# -------------------------------------------------------------

# --- CONFIGURATION ---
class Config:
    """Configuration class for the Flask application."""
    SECRET_KEY = secrets.token_urlsafe(32)
    
    # JWT Configuration
    JWT_SECRET_KEY = secrets.token_urlsafe(32)
    JWT_ALGORITHM = 'HS256'
    
    # Expiration Times
    ACCESS_TOKEN_EXPIRATION = timedelta(minutes=5)
    REFRESH_TOKEN_EXPIRATION = timedelta(days=30)
    
    # Environment/Debugging Flags
    DEBUG = True 
    TESTING = False 
    
    # Mock Database removed

# --- APPLICATION INITIALIZATION ---
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']


# --- UTILS: JWT HANDLING ---

def create_token(user_id, token_type):
    """Generates an Access Token or a Refresh Token."""
    
    if token_type == 'access':
        delta = app.config['ACCESS_TOKEN_EXPIRATION']
    elif token_type == 'refresh':
        delta = app.config['REFRESH_TOKEN_EXPIRATION']
    else:
        raise ValueError("Invalid token type")
    
    payload = {
        'sub': user_id,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + delta,
        'type': token_type 
    }
    
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['JWT_ALGORITHM'])

def validate_token(token, token_type):
    """Validates the token signature and expiration, checking for correct type."""
    try:
        payload = jwt.decode(
            token, 
            app.config['JWT_SECRET_KEY'], 
            algorithms=[app.config['JWT_ALGORITHM']]
        )
        
        if payload.get('type') != token_type:
            print(f"Validation failed: Token is a '{payload.get('type')}' token, expected '{token_type}'")
            return None
            
        return payload.get('sub')
        
    except jwt.ExpiredSignatureError:
        print(f"Validation failed: {token_type.capitalize()} token expired.")
        return 'expired'
    except jwt.InvalidTokenError:
        print(f"Validation failed: Invalid {token_type} token.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during validation: {e}")
        return None

# --- ROUTES: APPLICATION FLOW ---

@app.route('/')
def index():
    """Renders the login page."""
    refresh_token = request.cookies.get('refresh_token')
    if refresh_token:
        # Tries to perform silent login via refresh token
        return redirect(url_for('refresh_access'))
        
    # Render the separate index.html file from the 'templates' folder
    return render_template('index.html')

# --- NEW ROUTE: Serve the Registration Page ---
@app.route('/register', methods=['GET'])
def register():
    """Renders the registration page."""
    return render_template('register.html')

# --- NEW ROUTE: Handle Registration Submission ---
@app.route('/register', methods=['POST'])
def register_submit():
    """Handles new user registration using Firestore."""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    # NOTE: You should add password complexity checks here.

    success, message = register_new_user(username, password)

    if success:
        return jsonify({'message': f'User {username} registered successfully! You can now log in.'}), 201
    else:
        # Use 409 Conflict if the user already exists, 500 otherwise
        status_code = 409 if "already exists" in message else 500
        return jsonify({'message': message}), status_code


@app.route('/login', methods=['POST'])
def login():
    """Handles user authentication and issues the initial tokens using Firestore."""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Use Firestore utility function for verification
    user_id = verify_user_credentials(username, password)

    if user_id:
        
        access_token = create_token(user_id, 'access')
        refresh_token = create_token(user_id, 'refresh')
        
        access_exp = datetime.now(timezone.utc) + app.config['ACCESS_TOKEN_EXPIRATION']
        refresh_exp = datetime.now(timezone.utc) + app.config['REFRESH_TOKEN_EXPIRATION']
        print(f"[AUTH] User {user_id} logged in. Access expires at: {access_exp.strftime('%H:%M:%S')} UTC")
        
        response = jsonify({
            'message': 'Login successful', 
            'access_token': access_token,
            'user_id': user_id
        })
        
        # Set the Refresh Token as an HTTP-only cookie
        response.set_cookie(
            'refresh_token', 
            refresh_token, 
            httponly=True, 
            secure=app.config['TESTING'] == False and app.config['DEBUG'] == False,
            expires=refresh_exp
        )

        return response, 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/refresh', methods=['GET'])
def refresh_access():
    """Endpoint to exchange a valid Refresh Token for a new Access Token."""
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        print("[REFRESH] No refresh token found in cookies. Redirecting to login.")
        return redirect(url_for('index'))
    
    user_id = validate_token(refresh_token, 'refresh')

    if user_id and user_id != 'expired':
        new_access_token = create_token(user_id, 'access')
        
        # Store the new Access Token in the session
        session['access_token'] = new_access_token
        
        print(f"[REFRESH] Successfully issued new Access Token for {user_id}. Redirecting to dashboard.")
        # After refresh, the user goes to the protected area
        return redirect(url_for('dashboard'))

    # If the token is expired or invalid, clear the cookie and redirect to login
    response = redirect(url_for('index'))
    response.delete_cookie('refresh_token')
    return response

@app.route('/dashboard')
def dashboard():
    """A protected route requiring a valid Access Token."""
    
    access_token = session.get('access_token')
    
    if not access_token:
        print("[DASHBOARD] No access token in session. Trying to refresh.")
        return redirect(url_for('refresh_access'))
        
    user_id = validate_token(access_token, 'access')

    if user_id == 'expired':
        # Access Token expired! Initiate the silent refresh
        print("[DASHBOARD] Access token expired! Redirecting to refresh.")
        return redirect(url_for('refresh_access'))
        
    elif user_id:
        # Token is valid and non-expired. Grant access.
        print(f"[DASHBOARD] Access granted for {user_id}.")
        # Render the separate dashboard.html file
        return render_template('dashboard.html', user_id=user_id, access_expiration_minutes=int(app.config['ACCESS_TOKEN_EXPIRATION'].total_seconds() / 60))
        
    else:
        # Token is invalid or missing (unauthorized)
        print("[DASHBOARD] Invalid access token. Redirecting to login.")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Logs the user out by clearing all tokens."""
    session.pop('access_token', None)
    
    response = redirect(url_for('index'))
    # Crucially, delete the Refresh Token cookie to end the long-term session
    response.delete_cookie('refresh_token')
    
    print("[LOGOUT] Session ended and Refresh Token cookie deleted.")
    return response

if __name__ == '__main__':
    # Initialize Firestore BEFORE running the app to ensure connection is ready
    initialize_firestore()
    print("---------------------------------------------------------")
    print(f"| RUNNING FLASK APP")
    print("---------------------------------------------------------")
    app.run(debug=app.config['DEBUG'])