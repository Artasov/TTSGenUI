import os

from TTS.api import TTS  # noqa

os.makedirs("../output", exist_ok=True)


def generate_audio(
        text: str,
        model_name: str,
        output_path: str,
        gpu: bool = True,
        speaker_wav: str = None,
        language: str = None
):
    """
    Generate audio from text using Coqui TTS.
    @param text: Text to generate audio from.
    @param model_name: Model name to use.
    @param output_path: Path to save the audio.
    @param gpu: Whether to use GPU.
    @param speaker_wav: Path to speaker audio file for voice cloning.
    @param language: Language code for multilingual models.
    @return: None
    """
    tts = TTS(model_name, gpu=gpu)

    # Подготавливаем параметры для генерации
    tts_params = {
        'text': text,
        'file_path': output_path
    }

    # Добавляем speaker_wav если предоставлен (для клонирования голоса)
    if speaker_wav and os.path.exists(speaker_wav):
        tts_params['speaker_wav'] = speaker_wav
        print(f'🎯 Using speaker sample: {speaker_wav}')

    # Добавляем language если предоставлен
    if language:
        tts_params['language'] = language
        print(f'🌍 Using language: {language}')

    # Для многоязычных моделей без speaker_wav используем default speaker
    if not speaker_wav and 'multilingual' in model_name:
        # Определяем доступных спикеров для модели
        try:
            speakers = tts.speakers
            if speakers and len(speakers) > 0:
                tts_params['speaker'] = speakers[0]  # Используем первого доступного спикера
                print(f"🎯 Using default speaker: {speakers[0]}")
        except:  # noqa
            pass

    tts.tts_to_file(**tts_params)
    print(f"✅ Audio saved: {output_path}")
