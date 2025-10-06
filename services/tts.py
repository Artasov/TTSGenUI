import os

from TTS.api import TTS

os.makedirs("../output", exist_ok=True)

def generate_audio(text: str, model_name: str, output_path: str, gpu: bool = True):
    """
    Generate audio from text using Coqui TTS.
    @param text: Text to generate audio from.
    @param model_name: Model name to use.
    @param output_path: Path to save the audio.
    @param gpu: Whether to use GPU.
    @return: None
    """
    tts = TTS(model_name, gpu=gpu)
    tts.tts_to_file(text=text, file_path=output_path)
    print(f"✅ Audio saved: {output_path}")
