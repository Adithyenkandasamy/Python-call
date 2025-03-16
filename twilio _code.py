from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os

# Replace with your Twilio credentials
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# Define a TwiML response for the call
def handle_call():
    response = VoiceResponse()
    # Use the <Say> verb to speak to the caller
    response.say('Hello, please speak your message.')
    
    # Use the <Record> verb to record the caller's message
    response.record(max_length=60, recording_status_callback='http://example.com/recording-callback')
    
    return str(response)

# Create a call
call = client.calls.create(
    from_='+1 601 654 5962',
    to='+91 6382841307',
    url='https://demo.twilio.com/welcome/voice/'
)
