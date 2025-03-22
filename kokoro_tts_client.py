import requests
import os

# Kokoro API details
KOKORO_API_URL = "http://127.0.0.1:8880/v1/audio/speech"

def generate_kokoro_tts(text, voice="am_adam", output_file="response.mp3"):
    """Generate speech using Kokoro TTS and return the file path."""
    payload = {
        "model": "kokoro",
        "input": text,
        "voice": voice,
        "response_format": "mp3"
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(KOKORO_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"✅ Voice response saved as {output_file}")
            return output_file  # Return the path to the generated file
        else:
            print(f"❌ Kokoro API Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error in Kokoro TTS request: {e}")
        return None
