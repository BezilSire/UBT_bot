import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

logger = logging.getLogger(__name__)

class FirebaseClient:
    def __init__(self):
        self.db = None
        try:
            cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
            if not cred_path:
                logger.error("FIREBASE_SERVICE_ACCOUNT_KEY_PATH not set in .env")
                raise ValueError("Firebase credentials path not provided.")

            if not os.path.exists(cred_path):
                logger.error(f"Firebase credentials file not found at: {cred_path}")
                raise ValueError(f"Firebase credentials file not found at: {cred_path}")

            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully.")
            else:
                logger.info("Firebase Admin SDK already initialized.")

            self.db = firestore.client()
            logger.info("Firestore client obtained successfully.")

        except ValueError as ve:
            logger.error(f"ValueError during Firebase initialization: {ve}")
            # Propagate error or handle as appropriate for your application
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during Firebase initialization: {e}")
            # Propagate error or handle
            raise

    def get_user(self, user_id):
        if not self.db:
            logger.error("Firestore client not initialized.")
            return None
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            if user_doc.exists:
                return user_doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def create_user(self, user_id, user_data):
        if not self.db:
            logger.error("Firestore client not initialized.")
            return False
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_ref.set(user_data, merge=True) # merge=True to update if exists, create if not
            logger.info(f"User {user_id} created/updated successfully with data: {user_data}")
            return True
        except Exception as e:
            logger.error(f"Error creating/updating user {user_id}: {e}")
            return False

    def add_vendor(self, vendor_data):
        if not self.db:
            logger.error("Firestore client not initialized.")
            return None
        try:
            # You might want to generate a unique ID or use user_id + business_name hash
            # For now, letting Firestore auto-generate ID for the vendor document
            doc_ref = self.db.collection('vendors').add(vendor_data)
            logger.info(f"Vendor added successfully with ID: {doc_ref[1].id} and data: {vendor_data}")
            return doc_ref[1].id # Return the new document ID
        except Exception as e:
            logger.error(f"Error adding vendor: {e}")
            return None

    def find_vendors(self, location_query=None, category_query=None):
        if not self.db:
            logger.error("Firestore client not initialized.")
            return []
        try:
            query = self.db.collection('vendors').where('status', '==', 'approved') # Only show approved vendors

            # This is a very basic search. Firestore is not great for complex geoqueries or full-text search.
            # For geoqueries, you'd typically use a geohashing library (e.g., geofirestore) or a dedicated search service like Algolia.
            # For text search on name/description, similar tools are needed.

            # Simple text search (case-insensitive might require storing a lower-case version of fields)
            # This example doesn't implement advanced searching for brevity.
            if location_query and isinstance(location_query, str):
                # This is a very basic text search. For better results, consider:
                # 1. Storing a 'searchable_location_text' field in lowercase.
                # 2. Using Firestore array-contains for keywords if location_query is tokenized.
                # 3. Integrating with a dedicated search service like Algolia or Elasticsearch.
                # For now, we'll try a simple substring match if possible, though Firestore is limited here.
                # A direct equality on a field like 'location_data.text' (if it's consistently the city/area)
                # or 'city_lowercase' (if we add it) is more likely to work with Firestore queries.
                # Let's assume for now we are trying to match 'location_data.text'.
                # Firestore doesn't support case-insensitive queries or substring matches directly on non-array fields.
                # So, this will be an exact match on 'location_data.text' if it's a string.
                # If location_query is GPS, this part will be skipped.
                pass # Placeholder - actual text search needs careful schema design or external service

            # If location_query is a dict (GPS), we can't directly query by proximity in Firestore without GeoFire or similar.
            # So, for GPS, we'd fetch all vendors (or by a broader region if possible) and filter client-side, which is not scalable.
            # For this iteration, if it's GPS, we won't filter by location in the query itself beyond 'approved'.
            # The text search above is also very limited.

            if category_query:
                query = query.where('category', '==', category_query)

            all_approved_vendors = []
            for doc in query.stream():
                vendor_dict = doc.to_dict()
                vendor_dict['id'] = doc.id
                all_approved_vendors.append(vendor_dict)

            vendors = []
            if location_query and isinstance(location_query, str) and location_query.strip():
                # Perform a manual, case-insensitive filter on the text location after fetching
                # This is inefficient for large datasets but works for smaller ones.
                search_term_lower = location_query.lower()
                for vendor in all_approved_vendors:
                    loc_data = vendor.get('location_data', {})
                    text_loc = loc_data.get('text', '')
                    if isinstance(text_loc, str) and search_term_lower in text_loc.lower():
                        vendors.append(vendor)
            elif location_query and isinstance(location_query, dict) and 'latitude' in location_query:
                # Basic GPS filtering: If GPS is provided, for now, we return all approved vendors
                # (optionally filtered by category). Real geo-filtering is complex.
                # A simple approach could be to add city/region to vendor data and match that if GPS is given.
                # For now, return all and mention that precise GPS filtering is not yet active.
                vendors = all_approved_vendors
            else: # No specific location query, or it's empty
                vendors = all_approved_vendors

            # If category was already filtered by Firestore, vendors list is now further filtered by text location if provided.
            # If only GPS location was provided, vendors list contains all approved (and category-filtered) vendors.

            logger.info(f"Found {len(vendors)} vendors after filtering for location '{location_query}' and category '{category_query}'. Initial count: {len(all_approved_vendors)}")
            for doc in query.stream():
                vendor_dict = doc.to_dict()
                vendor_dict['id'] = doc.id # Add document ID to the dict
                vendors.append(vendor_dict)

            logger.info(f"Found {len(vendors)} vendors matching query.")
            return vendors
        except Exception as e:
            logger.error(f"Error finding vendors: {e}")
            return []

    def find_user_by_referral_code(self, referral_code):
        if not self.db:
            logger.error("Firestore client not initialized.")
            return None
        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('referral_code', '==', referral_code).limit(1)
            results = query.stream()
            for doc in results:
                logger.info(f"Found user {doc.id} for referral code {referral_code}")
                return {'telegram_id': doc.id, **doc.to_dict()} # Return telegram_id and other data
            logger.info(f"No user found with referral code {referral_code}")
            return None
        except Exception as e:
            logger.error(f"Error finding user by referral code {referral_code}: {e}")
            return None

    def increment_referral_count(self, referrer_id):
        if not self.db: return False
        try:
            user_ref = self.db.collection('users').document(str(referrer_id))
            user_ref.update({'referral_count': firestore.Increment(1)})
            logger.info(f"Incremented referral count for user {referrer_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing referral count for {referrer_id}: {e}")
            return False

    def add_referral_reward(self, referrer_id, reward_amount):
        if not self.db: return False
        try:
            user_ref = self.db.collection('users').document(str(referrer_id))
            # This assumes 'referral_rewards_balance' and 'ubt_balance' exist or are created
            # You might want separate fields for total rewards vs claimable rewards
            user_ref.update({
                'referral_rewards_balance': firestore.Increment(reward_amount),
                'ubt_balance': firestore.Increment(reward_amount) # Or add to a separate rewards pool first
            })
            logger.info(f"Added {reward_amount} UBT referral reward to user {referrer_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding referral reward for {referrer_id}: {e}")
            return False

# Example usage (for testing locally, not part of the bot's runtime flow directly here):
# if __name__ == '__main__':
#     from dotenv import load_dotenv
#     load_dotenv(dotenv_path='../../.env') # Adjust path as needed
#
#     logger.info("Attempting to initialize FirebaseClient for standalone test...")
#     try:
#         client = FirebaseClient()
#         if client.db:
#             logger.info("FirebaseClient initialized. Firestore DB is available.")
#             # Test creating a user
#             # test_user_id = "test_user_123"
#             # test_user_data = {"name": "Test User", "phone": "1234567890", "referral_code": "TESTREF123"}
#             # client.create_user(test_user_id, test_user_data)
#             # fetched_user = client.get_user(test_user_id)
#             # print(f"Fetched user: {fetched_user}")
#         else:
#             logger.error("FirebaseClient initialized, but Firestore DB is NOT available.")
#     except Exception as e:
#         logger.error(f"Failed to initialize FirebaseClient for standalone test: {e}", exc_info=True)

```
