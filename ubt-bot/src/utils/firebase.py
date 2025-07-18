import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def initialize_firebase():
    """
    Initializes the Firebase app.
    """
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

def get_user_details(user_id):
    """
    Gets the user's details from Firebase.
    """
    db = firestore.client()
    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None

def store_user_details(user_id, user_details):
    """
    Stores the user's details in Firebase.
    """
    db = firestore.client()
    db.collection("users").document(user_id).set(user_details)
