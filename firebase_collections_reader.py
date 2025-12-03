import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from dotenv import load_dotenv

def initialize_firebase(service_account_path):
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    Args:
        service_account_path: Path to your Firebase service account JSON file
    """
    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        print("✓ Firebase initialized successfully\n")
    except Exception as e:
        print(f"✗ Error initializing Firebase: {e}")
        exit(1)

def get_all_collections_and_fields(db):
    """
    Retrieve all collections and their fields from Firestore.
    
    Args:
        db: Firestore client instance
    """
    print("=" * 80)
    print("FIREBASE FIRESTORE DATABASE STRUCTURE")
    print("=" * 80)
    print()
    
    # Get all root-level collections
    collections = db.collections()
    
    for collection in collections:
        collection_name = collection.id
        print(f"📁 Collection: {collection_name}")
        print("-" * 80)
        
        # Get all documents in the collection
        docs = collection.limit(10).stream()  # Limit to first 10 docs to avoid overwhelming output
        
        doc_count = 0
        all_fields = set()
        
        for doc in docs:
            doc_count += 1
            doc_dict = doc.to_dict()
            
            if doc_count == 1:
                # Print first document as example
                print(f"\n  📄 Example Document ID: {doc.id}")
                print(f"  Fields in this document:")
                
                for field_name, field_value in doc_dict.items():
                    field_type = type(field_value).__name__
                    all_fields.add(field_name)
                    
                    # Truncate long values for display
                    display_value = str(field_value)
                    if len(display_value) > 50:
                        display_value = display_value[:50] + "..."
                    
                    print(f"    • {field_name}: {field_type} = {display_value}")
            else:
                # Just collect field names from other documents
                for field_name in doc_dict.keys():
                    all_fields.add(field_name)
            
            # Check for subcollections
            subcollections = db.collection(collection_name).document(doc.id).collections()
            for subcol in subcollections:
                print(f"\n    📁 Subcollection: {collection_name}/{doc.id}/{subcol.id}")
        
        # Print summary
        print(f"\n  📊 Summary:")
        print(f"    • Total documents sampled: {doc_count}")
        print(f"    • Unique fields found: {', '.join(sorted(all_fields))}")
        print()
        print("=" * 80)
        print()

def main():
    """
    Main function to run the Firebase database reader.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get service account path from environment variable
    SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    
    if not SERVICE_ACCOUNT_PATH:
        print("❌ Error: FIREBASE_SERVICE_ACCOUNT_PATH not found in .env file")
        print("Please create a .env file with:")
        print("FIREBASE_SERVICE_ACCOUNT_PATH=path/to/your/serviceAccountKey.json")
        exit(1)
    
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(f"❌ Error: Service account file not found at: {SERVICE_ACCOUNT_PATH}")
        print("Please check the path in your .env file")
        exit(1)
    
    print("\n🔥 Firebase Database Collections Reader")
    print("=" * 80)
    print()
    
    # Initialize Firebase
    initialize_firebase(SERVICE_ACCOUNT_PATH)
    
    # Get Firestore client
    db = firestore.client()
    
    # Retrieve and print all collections and fields
    get_all_collections_and_fields(db)
    
    print("\n✓ Database structure retrieval complete!")

if __name__ == "__main__":
    main()
