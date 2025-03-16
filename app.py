from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import requests
from dotenv import load_dotenv
import openai

load_dotenv()

app = Flask(__name__)

# Twilio Credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
FROM_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TO_NUMBER = os.getenv('MY_PHONE_NUMBER')

client = Client(account_sid, auth_token)

# GitHub Marketplace AI API
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ENDPOINT = "https://models.inference.ai.azure.com"
MODEL_NAME = "gpt-4o"

# Faster Whisper API URL
FASTER_WHISPER_URL = "http://127.0.0.1:8000/transcriptions"

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    response.say("Hello! Speak and I will respond in real-time.")
    response.record(
        max_length=10, 
        recording_status_callback="/recording_status", 
        play_beep=True
    )
    return str(response)

@app.route("/recording_status", methods=['POST'])
def recording_status():
    recording_url = request.form.get("RecordingUrl") + ".mp3"
    print(f"Recording available at: {recording_url}")

    # Transcribe the audio using Faster Whisper API
    transcript = transcribe_with_faster_whisper(recording_url)
    print("User said:", transcript)

    # Get AI response
    ai_response = get_ai_response(transcript)
    print("AI Response:", ai_response)

    # Call back with AI response
    respond_with_voice(ai_response)

    return "OK", 200

# Send audio file to Faster Whisper API
def transcribe_with_faster_whisper(audio_url):
    audio_path = "recorded_audio.mp3"

    # Download the audio file
    response = requests.get(audio_url)
    with open(audio_path, "wb") as f:
        f.write(response.content)

    # Send the file to Faster Whisper API
    with open(audio_path, "rb") as audio_file:
        response = requests.post(FASTER_WHISPER_URL, files={"file": audio_file})

    if response.status_code == 200:
        result = response.json()
        return result.get("text", "Could not transcribe")
    else:
        return "Transcription failed"

# Get AI response from GPT-4o
def get_ai_response(user_text):
    try:
        client = openai.OpenAI(base_url=ENDPOINT, api_key=GITHUB_TOKEN)

        stream = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_text}
            ],
            model=MODEL_NAME,
            stream=True,
            stream_options={"include_usage": True}
        )

        response_text = ""
        for part in stream:
            if part.choices:  # ✅ Check if choices exist
                response_text += part.choices[0].delta.content or ""  # ✅ FIXED!

        return response_text.strip() if response_text else "No response received."

    except Exception as e:
        print("Error in AI response:", str(e))
        return "I'm sorry, I couldn't process that."

# Call back and speak the AI response
def respond_with_voice(text):
    call = client.calls.create(
        from_=FROM_NUMBER,
        to=TO_NUMBER,
        url="https://795c-152-58-248-235.ngrok-free.app/speak",
        method="POST",
        send_digits="1"
    )
    print("Callback initiated:", call.sid)

@app.route("/speak", methods=['POST'])
def speak():
    data = request.get_json()
    text = data.get("text", "I'm sorry, I didn't understand.")
    
    response = VoiceResponse()
    response.say(text)
    
    return str(response)

# Function to initiate call
def make_call():
    call = client.calls.create(
        from_=FROM_NUMBER,
        to=TO_NUMBER,
        url="https://795c-152-58-248-235.ngrok-free.app/voice",
        method="POST"
    )
    print("Call initiated: ", call.sid)

if __name__ == "__main__":
    print("Starting server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
