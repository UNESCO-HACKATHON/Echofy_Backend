import os
from dotenv import load_dotenv
import assemblyai as aai

load_dotenv()
aai.settings.api_key = os.getenv("ASSEMBLY_AI_API")

def transcribe_audio(audio_file_path):
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
    print("Transcription started. This might take some time; we will inform you when complete.")
    transcript = aai.Transcriber(config=config).transcribe(audio_file_path)

    if transcript.status == "error":
        raise Exception(f"Transcription failed: {transcript.error}")
    return transcript.text