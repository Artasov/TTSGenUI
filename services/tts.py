import os
import sys
from io import StringIO

from TTS.api import TTS  # noqa

os.makedirs("../output", exist_ok=True)

# Автоматически соглашаемся с лицензией XTTS v2
def auto_accept_license():
    """Автоматически принимает лицензионные условия для XTTS v2"""
    # Устанавливаем переменную окружения для автоматического принятия лицензии
    os.environ['COQUI_TOS_AGREED'] = '1'
    original_stdin = sys.stdin
    sys.stdin = StringIO('y\n')
    return original_stdin

def restore_stdin(original_stdin):
    """Восстанавливает оригинальный stdin"""
    sys.stdin = original_stdin


def generate_audio(
        text: str,
        model_name: str,
        output_path: str,
        gpu: bool = True,
        speaker_wav: str = None,
        language: str = None,
        speaker: str = None
):
    """
    Generate audio from text using Coqui TTS.
    @param text: Text to generate audio from.
    @param model_name: Model name to use.
    @param output_path: Path to save the audio.
    @param gpu: Whether to use GPU.
    @param speaker_wav: Path to speaker audio file for voice cloning.
    @param language: Language code for multilingual models.
    @param speaker: Speaker name for multi-speaker models.
    @return: None
    """
    # Автоматически принимаем лицензию для XTTS v2
    original_stdin = None
    if 'xtts' in model_name.lower():
        original_stdin = auto_accept_license()
    
    try:
        print(f"🔄 Loading TTS model: {model_name}")
        tts = TTS(model_name)
        print(f"✅ Model loaded successfully")
        
        # Используем новый API вместо устаревшего параметра gpu
        if gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    tts.to('cuda')
                    print('🚀 Using GPU acceleration')
                else:
                    print('⚠️ GPU not available, using CPU')
            except ImportError:
                print('⚠️ PyTorch not available, using CPU')
        else:
            tts.to('cpu')
            print('💻 Using CPU')
            
        # Проверяем доступные атрибуты модели
        print(f"📋 Model attributes: speakers={hasattr(tts, 'speakers')}, language={hasattr(tts, 'language')}")
        
    except Exception as e:
        print(f"❌ Error initializing TTS: {e}")
        print(f"📋 Model name: {model_name}")
        raise
    finally:
        if original_stdin:
            restore_stdin(original_stdin)

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

    # Специальная обработка для XTTS v2
    if 'xtts' in model_name.lower():
        # XTTS v2 требует speaker_wav для клонирования голоса
        if not speaker_wav:
            # Если нет образца голоса, используем встроенные спикеры
            try:
                speakers = tts.speakers
                if speakers and len(speakers) > 0:
                    tts_params['speaker'] = speakers[0]
                    print(f"🎯 Using default XTTS speaker: {speakers[0]}")
            except:  # noqa
                pass
    else:
        # Добавляем speaker если предоставлен (для моделей с множественными спикерами)
        if speaker:
            tts_params['speaker'] = speaker
            print(f'🎤 Using speaker: {speaker}')
        elif not speaker_wav and 'multilingual' in model_name:
            # Для многоязычных моделей без speaker_wav используем default speaker
            try:
                speakers = tts.speakers
                if speakers and len(speakers) > 0:
                    tts_params['speaker'] = speakers[0]  # Используем первого доступного спикера
                    print(f"🎯 Using default speaker: {speakers[0]}")
            except:  # noqa
                pass

    try:
        print(f"🎵 Generating audio with parameters: {tts_params}")
        tts.tts_to_file(**tts_params)
        print(f"✅ Audio saved: {output_path}")
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        print(f"📋 Parameters used: {tts_params}")
        raise
