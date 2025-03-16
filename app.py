from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import requests
from dotenv import load_dotenv
import openai
import time

# Load environment variables
load_dotenv()

# Twilio Credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
FROM_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TO_NUMBER = os.getenv('MY_PHONE_NUMBER')

# Validate required environment variables
if not all([account_sid, auth_token, FROM_NUMBER, TO_NUMBER]):
    raise ValueError("⚠️ Missing Twilio credentials. Check your .env file.")

client = Client(account_sid, auth_token)

# GitHub Marketplace AI API
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ENDPOINT = "https://models.inference.ai.azure.com"
MODEL_NAME = "gpt-4o"

if not GITHUB_TOKEN:
    raise ValueError("⚠️ Missing GITHUB_TOKEN. Check your .env file.")

# Faster Whisper API URL (For Speech-to-Text)
FASTER_WHISPER_URL = "http://127.0.0.1:8000/transcriptions"

# NGROK URL (Dynamic)
NGROK_URL = os.getenv("NGROK_URL")
if not NGROK_URL:
    raise ValueError("⚠️ Missing NGROK_URL. Add it to your .env file.")

app = Flask(__name__)

# ============================
# 🔹 Step 1: Start a Voice Call & Record
# ============================
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    
    response.say("Hello! Speak as long as you need, then stop. I will answer after that.")
    
    response.record(
        timeout=5,  # Stops recording after 5 seconds of silence
        recording_status_callback=f"{NGROK_URL}/recording_status",
        play_beep=True
    )
    
    return str(response)

# ============================
# 🔹 Step 2: Handle Recorded Audio
# ============================
@app.route("/recording_status", methods=['POST'])
def recording_status():
    recording_url = request.form.get("RecordingUrl") + ".mp3"
    print(f"📢 Recording available at: {recording_url}")

    # Step 2.1: Transcribe using Faster Whisper API
    transcript = transcribe_with_faster_whisper(recording_url)
    print("🎙 User said:", transcript)

    # Step 2.2: Get AI Response
    ai_response = get_ai_response(transcript)
    print("🤖 AI Response:", ai_response)

    # Step 2.3: Call back with AI response
    respond_with_voice(ai_response)

    return "OK", 200

# ============================
# 🔹 Step 3: Transcribe with Faster Whisper
# ============================
def transcribe_with_faster_whisper(audio_url):
    audio_path = "recorded_audio.mp3"
    
    try:
        # Download the audio file (Retry if fails)
        for _ in range(3):  
            response = requests.get(audio_url, timeout=10)
            if response.status_code == 200:
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                break
            time.sleep(2)  # Wait before retrying
        else:
            return "⚠️ Error: Unable to download audio"

        # Send the file to Faster Whisper API (Retry if fails)
        headers = {"accept": "application/json"}
        
        for _ in range(3):
            with open(audio_path, "rb") as audio_file:
                files = {"file": ("recorded_audio.mp3", audio_file, "audio/mp3")}
                response = requests.post(FASTER_WHISPER_URL, files=files, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return result.get("text", "⚠️ Transcription issue")
            time.sleep(2)  # Retry delay

    except Exception as e:
        print(f"⚠️ Transcription Error: {e}")
        return "⚠️ Transcription failed"

    return "⚠️ Transcription failed"

# ============================
# 🔹 Step 4: Get AI Response from GPT-4o
# ============================
def get_ai_response(user_text):
    if not user_text or user_text == "⚠️ Transcription failed":
        return "⚠️ Sorry, I couldn't understand your request."

    try:
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_text}
            ],
            api_key=GITHUB_TOKEN
        )

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"⚠️ AI Request Error: {e}")
        return "⚠️ Error processing AI response."

# ============================
# 🔹 Step 5: Call Back & Speak AI Response
# ============================
def respond_with_voice(text):
    try:
        call = client.calls.create(
            from_=FROM_NUMBER,
            to=TO_NUMBER,
            url=f"{NGROK_URL}/speak?text={text}"
        )
        print("📞 Callback initiated:", call.sid)

    except Exception as e:
        print(f"⚠️ Call Error: {e}")

@app.route("/speak", methods=['GET'])
def speak():
    text = request.args.get("text", "I'm sorry, I didn't understand.")
    response = VoiceResponse()
    response.say(text)
    return str(response)

# ============================
# 🔹 Step 6: Function to Initiate Call
# ============================
def make_call():
    try:
        call = client.calls.create(
            from_=FROM_NUMBER,
            to=TO_NUMBER,
            url=f"{NGROK_URL}/voice"
        )
        print("📞 Call initiated: ", call.sid)

    except Exception as e:
        print(f"⚠️ Call Error: {e}")

# ============================
# 🔹 Start Flask Server
# ============================
if __name__ == "__main__":
    print("🚀 Starting server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
