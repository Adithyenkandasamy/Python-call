from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Twilio Credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
FROM_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TO_NUMBER = os.getenv('MY_PHONE_NUMBER')

client = Client(account_sid, auth_token)

# Handle the call and record user response
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    response = VoiceResponse()
    
    # Twilio says something and records response
    response.say("Hello! Please say something after the beep.")
    response.record(max_length=10, transcribe=True, transcribe_callback="/transcribe")
    
    return str(response)

# Get transcription from Twilio
@app.route("/transcribe", methods=['POST'])
def transcribe():
    transcript = request.form.get("TranscriptionText")
    
    print("\nUser said: ", transcript)  # Print user response in terminal
    
    return "OK", 200

# Function to initiate call
def make_call():
    call = client.calls.create(
        from_=FROM_NUMBER,
        to=TO_NUMBER,
        url="https://795c-152-58-248-235.ngrok-free.app/voice"  # Change to your actual public URL
    )
    print("Call initiated: ", call.sid)

if __name__ == "__main__":
    print("Starting server...")
    app.run(debug=True,host='0.0.0.0', port=5000)
