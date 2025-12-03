# 🔧 Setup Instructions - Chat Application

## Step 1: Add Groq API Key to .env file

1. Get your Groq API key from: https://console.groq.com/keys
2. Open your `.env` file (in `f:/WMSOLS/ammora/.env`)
3. Add this line at the end:

```
GROQ_API_KEY=your_actual_groq_api_key_here
```

Replace `your_actual_groq_api_key_here` with your actual API key from Groq.

Your `.env` file should look like this:

```env
FIREBASE_SERVICE_ACCOUNT_PATH=C:/Users/MSI/Downloads/testing-persona-firebase-adminsdk-fbsvc-ce9707d827.json
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 2: Upgrade Groq Package

Run this command to fix the version compatibility issue:

```bash
pip install --upgrade groq
```

Or if pip doesn't work, use:

```bash
python -m pip install --upgrade groq
```

## Step 3: Start the Server

After adding the API key and upgrading, run:

```bash
python app.py
```

You should see:
```
🚀 Starting Chat App Server...
📍 Server running at: http://localhost:5000
```

## Step 4: Open in Browser

Open your browser and go to:
```
http://localhost:5000
```

The chat application will load automatically!

---

## Troubleshooting

**Error: "GROQ_API_KEY not found"**
- Make sure you added the key to `.env` file (not `.env.example`)
- Make sure there are no extra spaces or quotes around the key

**Error: "TypeError: Client.__init__() got an unexpected keyword argument 'proxies'"**
- Run: `pip install --upgrade groq` to get the latest version

**Server won't start**
- Make sure no other application is using port 5000
- Check that Firebase credentials are correct in `.env`
