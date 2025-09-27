import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            # Try to use service account key file
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin initialized with service account")
            else:
                # Try to use environment variables for service account
                service_account_info = {
                    "type": "service_account",
                    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL')}"
                }
                
                # Check if we have all required fields
                if all(service_account_info.values()):
                    cred = credentials.Certificate(service_account_info)
                    firebase_admin.initialize_app(cred)
                    print("Firebase Admin initialized with environment variables")
                else:
                    print("Firebase Admin: Missing configuration, running without verification")
                    return None
                    
        except Exception as e:
            print(f"Firebase Admin initialization failed: {e}")
            print("Running without Firebase verification (development mode)")
            return None
    
    return firebase_admin.get_app()

def verify_firebase_token(token: str) -> Optional[dict]:
    """Verify Firebase ID token and return user data"""
    try:
        if not firebase_admin._apps:
            # If Firebase is not initialized, return mock data for development
            print("Warning: Firebase not initialized, using mock user data")
            return {
                "uid": "dev-user-123",
                "email": "dev@example.com",
                "name": "Development User"
            }
        
        print(f"Attempting to verify token: {token[:20]}...")  # Debug: show first 20 chars
        decoded_token = auth.verify_id_token(token)
        print(f"Token verified successfully for user: {decoded_token.get('email')}")  # Debug
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name", decoded_token.get("email", "Unknown User")),
        }
    except auth.InvalidIdTokenError as e:
        print(f"Invalid Firebase token: {e}")
        return None
    except auth.ExpiredIdTokenError as e:
        print(f"Expired Firebase token: {e}")
        return None
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

# Initialize Firebase on import
initialize_firebase()