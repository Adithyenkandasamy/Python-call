from faster_whisper import WhisperModel

def transcribe_audio(file_path, model_size="base"):
    """
    Transcribe audio file using Faster Whisper
    """
    # Load the Faster Whisper model
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    try:
        # Transcribe the audio
        segments, info = model.transcribe(
            file_path,
            language="en",
            vad_filter=False,
            vad_parameters=dict(min_silence_duration_ms=1000)
        )
        
        # Combine all segments into a single text
        result = " ".join([segment.text for segment in segments])
        return result
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def main():
    # Example usage
    file_path = '/home/jinwoo/Downloads/tmpqd0thkig.mp3'  # Replace with your audio file path
    result = transcribe_audio(file_path)
    if result:
        print("Transcription result:", result)

if __name__ == "__main__":
    main()