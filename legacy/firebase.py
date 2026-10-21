"""
Firebase Helper Module for Liver Buddy
Handles authentication and Firestore operations
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests
import json
from datetime import datetime

# Firebase Web API endpoint
FIREBASE_WEB_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", "")
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"

class FirebaseAuth:
    """Handle Firebase Authentication using REST API"""
    
    @staticmethod
    def sign_up(email, password):
        """Register a new user"""
        url = f"{FIREBASE_AUTH_URL}signUp?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "user_id": data["localId"],
                    "email": data["email"],
                    "token": data["idToken"]
                }
            else:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def sign_in(email, password):
        """Sign in existing user"""
        url = f"{FIREBASE_AUTH_URL}signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "user_id": data["localId"],
                    "email": data["email"],
                    "token": data["idToken"]
                }
            else:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

class FirestoreDB:
    """Handle Firestore database operations"""
    
    def __init__(self):
        # Initialize Firebase Admin if not already done
        try:
            # Check if already initialized
            firebase_admin.get_app()
        except ValueError:
            # Not initialized, so initialize it
            try:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
                firebase_admin.initialize_app(cred)
            except Exception as e:
                st.warning(f"Firebase initialization failed: {e}")
        
        try:
            self.db = firestore.client()
        except Exception as e:
            st.warning(f"Could not connect to Firestore: {e}")
            self.db = None
    
    def save_user_profile(self, user_id, data):
        """Save or update user profile"""
        if not self.db:
            return False
        
        try:
            self.db.collection('users').document(user_id).set(data, merge=True)
            return True
        except Exception as e:
            st.error(f"Error saving profile: {e}")
            return False
    
    def update_user_profile(self, user_id, data):
        """Update user profile (alias for save_user_profile with merge)"""
        if not self.db:
            return False
        
        try:
            self.db.collection('users').document(user_id).set(data, merge=True)
            return True
        except Exception as e:
            st.error(f"Error updating profile: {e}")
            return False
    
    def get_user_profile(self, user_id):
        """Get user profile data"""
        if not self.db:
            return None
        
        try:
            doc = self.db.collection('users').document(user_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            st.error(f"Error getting profile: {e}")
            return None
    
    def save_chat_history(self, user_id, message):
        """Save chat message to history"""
        if not self.db:
            return False
        
        try:
            self.db.collection('users').document(user_id).collection('chat_history').add({
                'message': message,
                'timestamp': datetime.now()
            })
            return True
        except Exception as e:
            st.error(f"Error saving chat: {e}")
            return False
    
    def get_chat_history(self, user_id, limit=50):
        """Retrieve chat history"""
        if not self.db:
            return []
        
        try:
            docs = (self.db.collection('users')
                   .document(user_id)
                   .collection('chat_history')
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .stream())
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Error getting chat history: {e}")
            return []
    
    def save_meal_plan(self, user_id, meal_plan):
        """Save meal plan"""
        if not self.db:
            return False
        
        try:
            meal_plan['timestamp'] = datetime.now()
            self.db.collection('users').document(user_id).collection('meal_plans').add(meal_plan)
            return True
        except Exception as e:
            st.error(f"Error saving meal plan: {e}")
            return False
    
    def save_meal_analysis(self, user_id, meal_data):
        """Save meal analysis (alias for save_meal_plan for consistency)"""
        if not self.db:
            return False
        
        try:
            meal_data['timestamp'] = datetime.now()
            self.db.collection('users').document(user_id).collection('meal_plans').add(meal_data)
            return True
        except Exception as e:
            st.error(f"Error saving meal analysis: {e}")
            return False
    
    def get_meal_plans(self, user_id, limit=10):
        """Get user's meal plans"""
        if not self.db:
            return []
        
        try:
            docs = (self.db.collection('users')
                   .document(user_id)
                   .collection('meal_plans')
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .stream())
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Error getting meal plans: {e}")
            return []
    
    def save_nutrition_log(self, user_id, log_entry):
        """Save nutrition log entry"""
        if not self.db:
            return False
        
        try:
            log_entry['timestamp'] = datetime.now()
            self.db.collection('users').document(user_id).collection('nutrition_logs').add(log_entry)
            return True
        except Exception as e:
            st.error(f"Error saving nutrition log: {e}")
            return False
    
    def get_nutrition_logs(self, user_id, start_date=None, end_date=None):
        """Get nutrition logs with optional date filtering"""
        if not self.db:
            return []
        
        try:
            query = self.db.collection('users').document(user_id).collection('nutrition_logs')
            
            if start_date:
                query = query.where('date', '>=', start_date)
            if end_date:
                query = query.where('date', '<=', end_date)
            
            docs = query.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Error getting nutrition logs: {e}")
            return []
    
    def save_risk_assessment(self, user_id, assessment):
        """Save health risk assessment"""
        if not self.db:
            return False
        
        try:
            assessment['timestamp'] = datetime.now()
            self.db.collection('users').document(user_id).collection('risk_assessments').add(assessment)
            return True
        except Exception as e:
            st.error(f"Error saving assessment: {e}")
            return False
    
    def get_latest_assessment(self, user_id):
        """Get most recent risk assessment"""
        if not self.db:
            return None
        
        try:
            docs = (self.db.collection('users')
                   .document(user_id)
                   .collection('risk_assessments')
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(1)
                   .stream())
            
            for doc in docs:
                return doc.to_dict()
            return None
        except Exception as e:
            st.error(f"Error getting assessment: {e}")
            return None
    
    def save_workout_plan(self, user_id, workout_data):
        """Save workout plan"""
        if not self.db:
            return False
        
        try:
            workout_data['timestamp'] = datetime.now()
            self.db.collection('users').document(user_id).collection('workout_plans').add(workout_data)
            return True
        except Exception as e:
            st.error(f"Error saving workout plan: {e}")
            return False
    
    def get_workout_plans(self, user_id, limit=10):
        """Get user's workout plans"""
        if not self.db:
            return []
        
        try:
            docs = (self.db.collection('users')
                   .document(user_id)
                   .collection('workout_plans')
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .stream())
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Error getting workout plans: {e}")
            return []
    
    def save_medication(self, user_id, med_data):
        """Save medication"""
        if not self.db:
            return False
        
        try:
            med_data['timestamp'] = datetime.now()
            self.db.collection('users').document(user_id).collection('medications').add(med_data)
            return True
        except Exception as e:
            st.error(f"Error saving medication: {e}")
            return False
    
    def get_medications(self, user_id, limit=50):
        """Get user's medications"""
        if not self.db:
            return []
        
        try:
            docs = (self.db.collection('users')
                   .document(user_id)
                   .collection('medications')
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .stream())
            
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Error getting medications: {e}")
            return []

# Convenience functions for Streamlit
def init_firebase():
    """Initialize Firebase in Streamlit app"""
    if 'firebase_db' not in st.session_state:
        st.session_state.firebase_db = FirestoreDB()
    return st.session_state.firebase_db

def login_user(email, password):
    """Login user and store credentials in session"""
    result = FirebaseAuth.sign_in(email, password)
    
    if result["success"]:
        st.session_state.logged_in = True
        st.session_state.user_id = result["user_id"]
        st.session_state.user_email = result["email"]
        st.session_state.user_token = result["token"]
        
        # Load user profile
        db = init_firebase()
        profile = db.get_user_profile(result["user_id"])
        
        if profile:
            st.session_state.user_profile = profile
            # Update last login
            db.save_user_profile(result["user_id"], {"last_login": datetime.now()})
        else:
            # Create basic profile if missing
            st.session_state.user_profile = {
                "email": result["email"],
                "fullName": result["email"].split('@')[0].title(),
                "created_at": datetime.now(),
                "last_login": datetime.now()
            }
            db.save_user_profile(result["user_id"], st.session_state.user_profile)
        
        return True, "Login successful!"
    else:
        error = result.get("error", "Login failed")
        # Make error messages more user-friendly
        if "INVALID_PASSWORD" in error or "INVALID_LOGIN_CREDENTIALS" in error:
            error = "Invalid email or password"
        elif "USER_NOT_FOUND" in error:
            error = "No account found with this email"
        elif "TOO_MANY_ATTEMPTS" in error:
            error = "Too many failed attempts. Please try again later"
        return False, error

def register_user(email, password, user_data=None):
    """Register new user with optional profile data"""
    result = FirebaseAuth.sign_up(email, password)
    
    if result["success"]:
        # Create user profile with provided data
        db = init_firebase()
        
        # Merge provided data with defaults
        profile_data = {
            "email": result["email"],
            "created_at": datetime.now(),
            "last_login": datetime.now()
        }
        
        if user_data:
            profile_data.update(user_data)
        
        db.save_user_profile(result["user_id"], profile_data)
        return True, "Registration successful! Please login."
    else:
        error = result.get("error", "Registration failed")
        # Make error messages more user-friendly
        if "EMAIL_EXISTS" in error:
            error = "This email is already registered"
        elif "WEAK_PASSWORD" in error:
            error = "Password should be at least 6 characters"
        elif "INVALID_EMAIL" in error:
            error = "Invalid email address"
        return False, error

def logout_user():
    """Logout user and clear session"""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_token = None
    st.session_state.user_profile = {}
    
    # Clear other session data
    for key in list(st.session_state.keys()):
        if key not in ['logged_in', 'user_id', 'user_email', 'user_token', 'user_profile']:
            del st.session_state[key]