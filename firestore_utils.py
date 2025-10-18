import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.exceptions import NotFound

# --- CONFIGURATION (NOW USING ENVIRONMENT VARIABLES) ---
# NOTE: The service account key components are now loaded from the environment 
# via the helper function in app.py. We no longer need FIREBASE_CREDENTIAL_PATH.
# ---------------------

_db = None

def initialize_firestore():
    """Initializes the Firebase Admin SDK and sets up the Firestore client using 
    credentials from environment variables (loaded via app.py).
    """
    global _db
    if _db is None:
        try:
            # 1. Load credential components from environment variables
            project_id = os.environ.get('FIREBASE_PROJECT_ID')
            client_email = os.environ.get('FIREBASE_CLIENT_EMAIL')
            private_key_raw = os.environ.get('FIREBASE_PRIVATE_KEY')
            
            if not all([project_id, client_email, private_key_raw]):
                print("[ERROR] Missing one or more Firebase credentials in environment variables.")
                return None

            # 2. Crucially, replace the raw string literal '\n' with actual newline characters
            # This is required for the private key format.
            private_key = private_key_raw.replace(r'\n', '\n')
            
            # 3. Construct the credentials dictionary
            cred_data = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token", # Good practice to include
            }

            # 4. Initialize the Certificate using the dictionary data
            cred = credentials.Certificate(cred_data)
            
            # 5. Initialize the app
            firebase_admin.initialize_app(cred, {'projectId': project_id})
            _db = firestore.client()
            print("[FIRESTORE] Initialization successful using environment variables.")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize Firebase: {e}")
            pass
    return _db

# --- The rest of the functions (get_firestore_db, register_new_user, verify_user_credentials) remain the same ---

def get_firestore_db():
    """Returns the initialized Firestore client instance."""
    if _db is None:
        return initialize_firestore()
    return _db

def register_new_user(user_id, password):
    """
    Adds a new user to the Firestore 'users' collection.
    
    NOTE: In a real application, you must HASH the password here before saving it!
    """
    db = get_firestore_db()
    if not db:
        return False, "Database not initialized"
        
    user_ref = db.collection('users').document(user_id)
    
    try:
        if user_ref.get().exists:
            return False, "User already exists"
            
        user_ref.set({
            'password': password, 
            'created_at': firestore.SERVER_TIMESTAMP,
            'is_admin': False
        })
        print(f"[FIRESTORE] User {user_id} registered.")
        return True, "Registration successful"
        
    except Exception as e:
        print(f"[ERROR] Firestore registration failed: {e}")
        return False, "Database error during registration"

def verify_user_credentials(user_id, password):
    """
    Checks Firestore for a user with the matching user_id and password.
    
    NOTE: This is a simplified check. A proper check would compare the password 
    against a stored hash.
    """
    db = get_firestore_db()
    if not db:
        print("[AUTH] Database not available.")
        return None
        
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            print(f"[AUTH] User {user_id} not found.")
            return None 
        
        user_data = user_doc.to_dict()
        
        # Simple password match (CHANGE THIS TO HASH COMPARISON IN PROD)
        if user_data.get('password') == password:
            print(f"[AUTH] Credentials valid for {user_id}.")
            return user_id
        else:
            print(f"[AUTH] Password mismatch for {user_id}.")
            return None 
            
    except NotFound:
        print(f"[AUTH] User document for {user_id} not found (unexpected error).")
        return None
    except Exception as e:
        print(f"[ERROR] Firestore authentication query failed: {e}")
        return None