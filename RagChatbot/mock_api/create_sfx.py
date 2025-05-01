from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

openai_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=openai_key
)

speech_file_path = Path(__file__).parent / "assets/sfx/speech.mp3"
with client.audio.speech.with_streaming_response.create(
  model="tts-1",
  voice="nova",
  input="hmmm?"
) as response:
    response.stream_to_file(speech_file_path)

