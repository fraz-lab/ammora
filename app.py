from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from groq import Groq
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize Firebase
print("🔥 Initializing Firebase...")

# Build credentials from environment variables
firebase_credentials = {
    "type": os.getenv("FIREBASE_TYPE", "service_account"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),  # Handle escaped newlines
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
}

# Validate required fields
required_fields = ["project_id", "private_key", "client_email"]
missing_fields = [field for field in required_fields if not firebase_credentials.get(field)]

if missing_fields:
    raise ValueError(f"Missing required Firebase credentials: {', '.join(missing_fields)}")

cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)
db = firestore.client()
print("✅ Firebase initialized successfully")

# Initialize Groq
print("🤖 Initializing Groq API...")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

groq_client = Groq(api_key=GROQ_API_KEY)
print("✅ Groq API initialized successfully")

# Serve the main HTML file
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Create or get user
@app.route('/api/user/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        username = data.get('username')
        age = data.get('age')
        
        if not username or not age:
            return jsonify({'error': 'Username and age are required'}), 400
        
        # Create user ID
        user_id = str(uuid.uuid4())
        
        # Create user document
        user_data = {
            'username': username,
            'age': int(age),
            'created_at': firestore.SERVER_TIMESTAMP,
            'persona_completed': False,
            'preferences': {}
        }
        
        db.collection('users').document(user_id).set(user_data)
        
        return jsonify({
            'user_id': user_id,
            'username': username,
            'message': 'User registered successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update user preferences
@app.route('/api/user/preferences', methods=['POST'])
def update_preferences():
    try:
        data = request.json
        user_id = data.get('user_id')
        preferences = data.get('preferences')
        
        if not user_id or not preferences:
            return jsonify({'error': 'User ID and preferences are required'}), 400
        
        # Update user preferences
        db.collection('users').document(user_id).update({
            'preferences': preferences,
            'persona_completed': True
        })
        
        return jsonify({'message': 'Preferences updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get user data
@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        user_data['user_id'] = user_id
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get chat history
@app.route('/api/messages/<user_id>', methods=['GET'])
def get_messages(user_id):
    try:
        # Get messages for this user (no ordering to avoid index requirement)
        messages_ref = db.collection('messages').where('userid', '==', user_id).stream()
        
        messages = []
        for msg in messages_ref:
            msg_data = msg.to_dict()
            messages.append({
                'role': msg_data.get('role'),
                'content': msg_data.get('content'),
                'timestamp': msg_data.get('timestamp')
            })
        
        # Sort by timestamp in Python
        messages.sort(key=lambda x: x.get('timestamp') or 0)
        
        return jsonify({'messages': messages}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        print("\n" + "="*50)
        print("📨 New chat request received")
        
        data = request.json
        user_id = data.get('user_id')
        user_message = data.get('message')
        
        print(f"👤 User ID: {user_id}")
        print(f"💬 Message: {user_message}")
        
        if not user_id or not user_message:
            print("❌ Missing user_id or message")
            return jsonify({'error': 'User ID and message are required'}), 400
        
        # Get user data
        print("🔍 Fetching user data from Firebase...")
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            print("❌ User not found in database")
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        print(f"✅ User data retrieved: {user_data.get('username')}")
        
        # Save user message to Firebase
        print("💾 Saving user message to Firebase...")
        user_msg_data = {
            'userid': user_id,
            'role': 'user',
            'content': user_message,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        db.collection('messages').add(user_msg_data)
        print("✅ User message saved")
        
        # Get conversation history
        print("📜 Fetching conversation history...")
        # Fetch without ordering to avoid index requirement
        messages_ref = db.collection('messages').where('userid', '==', user_id).stream()
        
        conversation_history = []
        for msg in messages_ref:
            msg_data = msg.to_dict()
            timestamp = msg_data.get('timestamp')
            conversation_history.append({
                'role': msg_data.get('role'),
                'content': msg_data.get('content'),
                'timestamp': timestamp
            })
        
        # Sort by timestamp in Python (newest first, then reverse for chronological order)
        conversation_history.sort(key=lambda x: x.get('timestamp') or 0)
        
        # Keep only last 20 messages
        conversation_history = conversation_history[-20:]
        
        # Remove timestamp from messages before sending to API
        conversation_history = [{'role': msg['role'], 'content': msg['content']} for msg in conversation_history]
        
        print(f"✅ Retrieved {len(conversation_history)} messages from history")
        
        # Build system prompt with user preferences
        preferences = user_data.get('preferences', {})
        username = user_data.get('username', 'User')
        
        system_prompt = f"""You are a warm, caring AI companion chatting with {username}.

User Information:
- Name: {username}
- Age: {user_data.get('age', 'Unknown')}

User Preferences:
"""
        
        if preferences:
            for key, value in preferences.items():
                if value:
                    system_prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        else:
            system_prompt += "- No preferences set yet\n"
        
        system_prompt += "\nBe a supportive companion, listen actively, show empathy, and engage in meaningful conversation based on their preferences."
        
        print("🤖 Calling Groq API...")
        
        # Prepare messages for Groq API
        api_messages = [{'role': 'system', 'content': system_prompt}]
        api_messages.extend(conversation_history)
        
        # Call Groq API
        chat_completion = groq_client.chat.completions.create(
            messages=api_messages,
            model="llama-3.3-70b-versatile",  # Meta Llama model
            temperature=0.7,
            max_tokens=1024,
        )
        
        assistant_message = chat_completion.choices[0].message.content
        print(f"✅ Groq API response received ({len(assistant_message)} chars)")
        
        # Save assistant message to Firebase
        print("💾 Saving assistant message to Firebase...")
        assistant_msg_data = {
            'userid': user_id,
            'role': 'assistant',
            'content': assistant_message,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        db.collection('messages').add(assistant_msg_data)
        print("✅ Assistant message saved")
        print("="*50 + "\n")
        
        return jsonify({
            'message': assistant_message,
            'model': 'llama-3.3-70b-versatile'
        }), 200
        
    except Exception as e:
        print("\n" + "="*50)
        print(f"❌ ERROR in chat endpoint: {type(e).__name__}")
        print(f"❌ Error message: {str(e)}")
        print("❌ Full traceback:")
        import traceback
        traceback.print_exc()
        print("="*50 + "\n")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Chat App Server...")
    print("📍 Server running at: http://localhost:5001")
    app.run(debug=True, port=5001)
