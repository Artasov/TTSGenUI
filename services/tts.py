import os
import sys
from io import StringIO

# Исправляем проблему с BeamSearchScorer в новых версиях transformers
def fix_transformers_compatibility():
    """Исправляет совместимость с новыми версиями transformers"""
    try:
        import transformers
        from transformers import __version__ as transformers_version
        
        # Проверяем версию transformers
        version_parts = transformers_version.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        # Если версия >= 4.40, добавляем заглушку для BeamSearchScorer
        if major > 4 or (major == 4 and minor >= 40):
            print("🔧 Исправление совместимости с transformers >= 4.40")
            
            # Добавляем заглушку для BeamSearchScorer
            import transformers.generation
            if not hasattr(transformers.generation, 'BeamSearchScorer'):
                class BeamSearchScorer:
                    def __init__(self, *args, **kwargs):
                        pass
                transformers.generation.BeamSearchScorer = BeamSearchScorer
                print("✅ Добавлена заглушка для BeamSearchScorer")
                
    except Exception as e:
        print(f"⚠️ Не удалось исправить совместимость: {e}")

# Применяем исправление при импорте
fix_transformers_compatibility()

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


def get_model_supported_languages(model_name: str):
    """Получает список поддерживаемых языков для модели"""
    # Словарь поддерживаемых языков для каждой модели
    model_languages = {
        'tts_models/multilingual/multi-dataset/xtts_v2': ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko', 'hi'],
        'tts_models/multilingual/multi-dataset/xtts_v1.1': ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko', 'hi'],
        'tts_models/multilingual/multi-dataset/your_tts': ['en', 'fr-fr', 'pt-br'],
        'tts_models/multilingual/multi-dataset/bark': ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko', 'hi'],
    }
    
    # Если модель не найдена в словаре, возвращаем None (неизвестно)
    return model_languages.get(model_name, None)

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
    # Проверяем поддержку языка для модели
    if language:
        supported_languages = get_model_supported_languages(model_name)
        if supported_languages and language not in supported_languages:
            # Предлагаем альтернативные модели для русского языка
            if language == 'ru':
                alternative_models = [
                    'tts_models/multilingual/multi-dataset/xtts_v2',
                    'tts_models/multilingual/multi-dataset/xtts_v1.1'
                ]
                raise ValueError(
                    f"Модель {model_name} не поддерживает русский язык (ru). "
                    f"Поддерживаемые языки: {supported_languages}. "
                    f"Для русского языка используйте: {', '.join(alternative_models)}"
                )
            else:
                raise ValueError(
                    f"Модель {model_name} не поддерживает язык '{language}'. "
                    f"Поддерживаемые языки: {supported_languages}"
                )
    
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
        
        # Специальная обработка для модели Bark
        if 'bark' in model_name.lower():
            print("🔧 Bark model failed, suggesting alternatives...")
            alternative_models = [
                'tts_models/multilingual/multi-dataset/xtts_v2',
                'tts_models/multilingual/multi-dataset/xtts_v1.1',
                'tts_models/multilingual/multi-dataset/your_tts'
            ]
            raise ValueError(
                f"Модель Bark повреждена или не может быть загружена. "
                f"Попробуйте альтернативные модели: {', '.join(alternative_models)}"
            )
        
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
        # XTTS v2 требует либо speaker_wav, либо speaker из доступных спикеров
        if not speaker_wav:
            # Пытаемся получить реальных спикеров
            try:
                speakers = tts.speakers
                if speakers and len(speakers) > 0:
                    print(f"📋 Available speakers: {speakers}")
                    # Если пользователь выбрал спикера, проверяем его наличие
                    if speaker and speaker in speakers:
                        tts_params['speaker'] = speaker
                        print(f"🎯 Using selected XTTS speaker: {speaker}")
                    else:
                        # Используем первого доступного спикера
                        first_speaker = list(speakers.keys())[0] if isinstance(speakers, dict) else speakers[0]
                        tts_params['speaker'] = first_speaker
                        print(f"🎯 Using first available XTTS speaker: {first_speaker}")
                else:
                    # Если нет встроенных спикеров, XTTS v2 требует speaker_wav
                    print(f"🎯 No built-in speakers found for XTTS, speaker_wav required")
                    if not speaker_wav:
                        raise ValueError("XTTS v2 не имеет встроенных спикеров. Пожалуйста, загрузите образец голоса (3-10 секунд аудио) или выберите другую модель.")
            except Exception as e:
                # Если ошибка получения спикеров, XTTS v2 требует speaker_wav
                print(f"🎯 Could not get XTTS speakers: {e}, speaker_wav required")
                if not speaker_wav:
                    raise ValueError("XTTS v2 не может получить список спикеров. Пожалуйста, загрузите образец голоса (3-10 секунд аудио) или выберите другую модель.")
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
                    first_speaker = list(speakers.keys())[0] if isinstance(speakers, dict) else speakers[0]
                    tts_params['speaker'] = first_speaker
                    print(f"🎯 Using multilingual speaker: {first_speaker}")
                else:
                    # Если нет встроенных спикеров, используем дефолтный
                    tts_params['speaker'] = 'female'
                    print(f"🎯 Using default speaker for multilingual model")
            except:  # noqa
                # В крайнем случае используем дефолтный спикер
                tts_params['speaker'] = 'female'
                print(f"🎯 Using fallback default speaker for multilingual model")

    try:
        print(f"🎵 Generating audio with parameters: {tts_params}")
        print(f"📋 Model: {model_name}")
        print(f"📋 Has speaker_wav: {bool(speaker_wav)}")
        print(f"📋 Has speaker: {bool(speaker)}")
        print(f"📋 Has language: {bool(language)}")
        
        tts.tts_to_file(**tts_params)
        print(f"✅ Audio saved: {output_path}")
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        print(f"📋 Parameters used: {tts_params}")
        print(f"📋 Model name: {model_name}")
        raise
