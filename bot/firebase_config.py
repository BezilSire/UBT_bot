import os
import json
import firebase_admin
from firebase_admin import credentials

# Load the JSON string from the Render environment variable
key_json = os.environ["FIREBASE_SERVICE_ACCOUNT_KEY"]

# Convert the JSON string into a dictionary
cred_dict = json.loads(key_json)

# Create a Firebase credential object from the dictionary
cred = credentials.Certificate(cred_dict)

# Initialize Firebase only if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
