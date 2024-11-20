import os
import sounddevice as sd
import numpy as np
import wave
from google.cloud import speech
import requests

# Configure environment variables
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path-to-your-google-credentials.json"

# GitHub OpenAI Marketplace Model API
GITHUB_MODEL_API_URL = "https://api.github.com/your-model-endpoint"
GITHUB_MODEL_API_TOKEN = "your-github-api-token"

# Recording settings
SAMPLE_RATE = 16000
DURATION = 5  # seconds


def record_audio():
    """Records audio from the microphone."""
    print("Recording...")
    audio_data = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    print("Recording complete.")
    return np.int16(audio_data.flatten())


def save_audio(filename, audio_data):
    """Saves recorded audio to a WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data)


def transcribe_audio(filename):
    """Transcribes audio using Google Speech-to-Text API."""
    client = speech.SpeechClient()

    with open(filename, "rb") as audio_file:
        audio_content = audio_file.read()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US",  # Change for desired language
    )

    response = client.recognize(config=config, audio=audio)
    return " ".join([result.alternatives[0].transcript for result in response.results])


def generate_response_with_github(prompt):
    """Generates a response using GitHub marketplace OpenAI model."""
    headers = {
        "Authorization": f"Bearer {GITHUB_MODEL_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "max_tokens": 150,
        "temperature": 0.7,
    }

    print("Thinking...")
    response = requests.post(GITHUB_MODEL_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json().get("choices")[0].get("text", "").strip()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return "I'm sorry, I couldn't generate a response."


def main():
    # Step 1: Record audio
    audio_data = record_audio()
    audio_file = "input_audio.wav"
    save_audio(audio_file, audio_data.tobytes())

    # Step 2: Transcribe audio
    try:
        transcription = transcribe_audio(audio_file)
        print(f"You said: {transcription}")
    except Exception as e:
        print(f"Error during transcription: {e}")
        return

    # Step 3: Generate response
    response = generate_response_with_github(transcription)
    print(f"Assistant: {response}")


if __name__ == "__main__":
    main()
