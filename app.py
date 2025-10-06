import os
import uuid
from pathlib import Path
from typing import List

# Настройка папки для кэша моделей TTS
MODELS_DIR = Path(__file__).parent / 'models'
MODELS_DIR.mkdir(exist_ok=True)
os.environ['TTS_HOME'] = str(MODELS_DIR)

# Автоматически соглашаемся с лицензией Coqui TTS
os.environ['COQUI_TOS_AGREED'] = '1'

# Проверяем совместимость зависимостей
def check_dependencies():
    """Проверяет совместимость зависимостей"""
    try:
        import transformers
        from transformers import __version__ as transformers_version
        
        version_parts = transformers_version.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        if major > 4 or (major == 4 and minor >= 40):
            print("⚠️ ВНИМАНИЕ: Обнаружена несовместимая версия transformers")
            print(f"📋 Текущая версия: {transformers_version}")
            print("💡 Рекомендуется: transformers==4.35.2")
            print("🔧 Запустите: python fix_dependencies.py")
            
    except ImportError:
        print("⚠️ Transformers не установлен")
    except Exception as e:
        print(f"⚠️ Ошибка проверки зависимостей: {e}")

# Проверяем зависимости при запуске
check_dependencies()

from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services.tts import generate_audio

app = FastAPI(title='TTS Generator')

# Настройка шаблонов
templates = Jinja2Templates(directory='templates')

# Настройка статических файлов
app.mount("/output", StaticFiles(directory="output"), name="output")

# Создаем папку output если её нет
os.makedirs('output', exist_ok=True)

# Создаем папку для загруженных файлов
UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

# Доступные модели TTS с подробными описаниями
AVAILABLE_MODELS = {
    '🌍 Многоязычные модели с клонированием голоса': [
        {
            'id': 'tts_models/multilingual/multi-dataset/xtts_v2',
            'name': 'XTTS v2 Multilingual',
            'description': 'XTTS-v2.0.3 by Coqui с поддержкой 17 языков и клонированием голоса',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': True,
            'speakers': True
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/xtts_v1.1',
            'name': 'XTTS v1.1 Multilingual',
            'description': 'XTTS-v1.1 с поддержкой 14 языков и клонированием голоса',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': True,
            'speakers': True
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/your_tts',
            'name': 'YourTTS Multilingual',
            'description': 'Your TTS модель с клонированием голоса и поддержкой множества языков',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': True,
            'speakers': True
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/bark',
            'name': 'Bark Multilingual',
            'description': '🐶 Bark TTS модель с эмоциями и клонированием голоса',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': True,
            'speakers': True
        }
    ],
    '🇺🇸 Английские модели': [
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DDC',
            'name': 'LJSpeech Tacotron2-DDC',
            'description': 'Tacotron2 с Double Decoder Consistency - высококачественная английская речь',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DDC_ph',
            'name': 'LJSpeech Tacotron2-DDC Phonemes',
            'description': 'Tacotron2 с Double Decoder Consistency и фонемами',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/glow-tts',
            'name': 'LJSpeech Glow-TTS',
            'description': 'Glow-TTS модель с контролем темпа речи',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/speedy-speech',
            'name': 'LJSpeech Speedy Speech',
            'description': 'Speedy Speech с Alignment Network для изучения длительностей',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'medium',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DCA',
            'name': 'LJSpeech Tacotron2-DCA',
            'description': 'Tacotron2 с Double Decoder Consistency',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/vits',
            'name': 'LJSpeech VITS',
            'description': 'VITS End2End TTS модель с фонемами',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/fast_pitch',
            'name': 'LJSpeech FastPitch',
            'description': 'FastPitch модель с Aligner Network',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'medium',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/overflow',
            'name': 'LJSpeech Overflow',
            'description': 'Overflow модель, обученная на LJSpeech',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ljspeech/neural_hmm',
            'name': 'LJSpeech Neural HMM',
            'description': 'Neural HMM модель, обученная на LJSpeech',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/vctk/vits',
            'name': 'VCTK VITS',
            'description': 'VITS модель с 109 различными спикерами с английским акцентом',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': True
        },
        {
            'id': 'tts_models/en/vctk/fast_pitch',
            'name': 'VCTK FastPitch',
            'description': 'FastPitch модель, обученная на VCTK датасете',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'medium',
            'voice_cloning': False,
            'speakers': True
        },
        {
            'id': 'tts_models/en/sam/tacotron-DDC',
            'name': 'Sam Tacotron-DDC',
            'description': 'Tacotron2 с Double Decoder Consistency, обученная на Sam датасете',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/blizzard2013/capacitron-t2-c50',
            'name': 'Blizzard2013 Capacitron-T2-C50',
            'description': 'Capacitron добавления к Tacotron 2 с Capacity 50',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/blizzard2013/capacitron-t2-c150_v2',
            'name': 'Blizzard2013 Capacitron-T2-C150 v2',
            'description': 'Capacitron добавления к Tacotron 2 с Capacity 150',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/multi-dataset/tortoise-v2',
            'name': 'Tortoise v2',
            'description': 'Tortoise TTS модель с высоким качеством',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/jenny/jenny',
            'name': 'Jenny VITS',
            'description': 'VITS модель, обученная на Jenny(Dioco) датасете',
            'language': 'en',
            'gender': 'female',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/en/ek1/tacotron2',
            'name': 'EK1 Tacotron2',
            'description': 'EK1 en-rp tacotron2 by NMStoker',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇩🇪 Немецкие модели': [
        {
            'id': 'tts_models/de/thorsten/tacotron2-DDC',
            'name': 'Thorsten Tacotron2-DDC',
            'description': 'Thorsten-Dec2021-22k-DDC - высококачественная немецкая речь',
            'language': 'de',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/de/thorsten/tacotron2-DCA',
            'name': 'Thorsten Tacotron2-DCA',
            'description': 'Tacotron2 с Double Decoder Consistency для немецкого языка',
            'language': 'de',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/de/thorsten/vits',
            'name': 'Thorsten VITS',
            'description': 'VITS модель для немецкого языка',
            'language': 'de',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/de/css10/vits-neon',
            'name': 'German CSS10 VITS-Neon',
            'description': 'VITS-Neon модель для немецкого языка',
            'language': 'de',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇫🇷 Французские модели': [
        {
            'id': 'tts_models/fr/mai/tacotron2-DDC',
            'name': 'MAI French Tacotron2-DDC',
            'description': 'Tacotron2 с Double Decoder Consistency для французского языка',
            'language': 'fr',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/fr/css10/vits',
            'name': 'French CSS10 VITS',
            'description': 'VITS модель для французского языка',
            'language': 'fr',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇪🇸 Испанские модели': [
        {
            'id': 'tts_models/es/mai/tacotron2-DDC',
            'name': 'MAI Spanish Tacotron2-DDC',
            'description': 'Tacotron2 с Double Decoder Consistency для испанского языка',
            'language': 'es',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/es/css10/vits',
            'name': 'Spanish CSS10 VITS',
            'description': 'VITS модель для испанского языка',
            'language': 'es',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇮🇹 Итальянские модели': [
        {
            'id': 'tts_models/it/mai_female/glow-tts',
            'name': 'MAI Italian Female Glow-TTS',
            'description': 'GlowTTS модель для итальянского языка (женский голос)',
            'language': 'it',
            'gender': 'female',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/it/mai_female/vits',
            'name': 'MAI Italian Female VITS',
            'description': 'VITS модель для итальянского языка (женский голос)',
            'language': 'it',
            'gender': 'female',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/it/mai_male/glow-tts',
            'name': 'MAI Italian Male Glow-TTS',
            'description': 'GlowTTS модель для итальянского языка (мужской голос)',
            'language': 'it',
            'gender': 'male',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/it/mai_male/vits',
            'name': 'MAI Italian Male VITS',
            'description': 'VITS модель для итальянского языка (мужской голос)',
            'language': 'it',
            'gender': 'male',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇯🇵 Японские модели': [
        {
            'id': 'tts_models/ja/kokoro/tacotron2-DDC',
            'name': 'Japanese Kokoro Tacotron2-DDC',
            'description': 'Tacotron2 с Double Decoder Consistency, обученная на Kokoro Speech Dataset',
            'language': 'ja',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇨🇳 Китайские модели': [
        {
            'id': 'tts_models/zh-CN/baker/tacotron2-DDC-GST',
            'name': 'Chinese Baker Tacotron2-DDC-GST',
            'description': 'Tacotron2 с Double Decoder Consistency и GST для китайского языка',
            'language': 'zh',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇳🇱 Голландские модели': [
        {
            'id': 'tts_models/nl/mai/tacotron2-DDC',
            'name': 'MAI Dutch Tacotron2-DDC',
            'description': 'Tacotron2 с Double Decoder Consistency для голландского языка',
            'language': 'nl',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/nl/css10/vits',
            'name': 'Dutch CSS10 VITS',
            'description': 'VITS модель для голландского языка',
            'language': 'nl',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇺🇦 Украинские модели': [
        {
            'id': 'tts_models/uk/mai/glow-tts',
            'name': 'MAI Ukrainian Glow-TTS',
            'description': 'GlowTTS модель для украинского языка',
            'language': 'uk',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/uk/mai/vits',
            'name': 'MAI Ukrainian VITS',
            'description': 'VITS модель для украинского языка',
            'language': 'uk',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇹🇷 Турецкие модели': [
        {
            'id': 'tts_models/tr/common-voice/glow-tts',
            'name': 'Turkish Common Voice Glow-TTS',
            'description': 'Турецкая GlowTTS модель с неизвестным спикером из Common-Voice датасета',
            'language': 'tr',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇵🇱 Польские модели': [
        {
            'id': 'tts_models/pl/mai_female/vits',
            'name': 'MAI Polish Female VITS',
            'description': 'VITS модель для польского языка (женский голос)',
            'language': 'pl',
            'gender': 'female',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🇧🇾 Белорусские модели': [
        {
            'id': 'tts_models/be/common-voice/glow-tts',
            'name': 'Belarusian Common Voice Glow-TTS',
            'description': 'Белорусская GlowTTS модель, созданная @alex73',
            'language': 'be',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ],
    '🌍 Другие языки': [
        {
            'id': 'tts_models/bg/cv/vits',
            'name': 'Bulgarian VITS',
            'description': 'VITS модель для болгарского языка',
            'language': 'bg',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/cs/cv/vits',
            'name': 'Czech VITS',
            'description': 'VITS модель для чешского языка',
            'language': 'cs',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/da/cv/vits',
            'name': 'Danish VITS',
            'description': 'VITS модель для датского языка',
            'language': 'da',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/et/cv/vits',
            'name': 'Estonian VITS',
            'description': 'VITS модель для эстонского языка',
            'language': 'et',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/ga/cv/vits',
            'name': 'Irish VITS',
            'description': 'VITS модель для ирландского языка',
            'language': 'ga',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/hu/css10/vits',
            'name': 'Hungarian VITS',
            'description': 'VITS модель для венгерского языка',
            'language': 'hu',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/el/cv/vits',
            'name': 'Greek VITS',
            'description': 'VITS модель для греческого языка',
            'language': 'el',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/fi/css10/vits',
            'name': 'Finnish VITS',
            'description': 'VITS модель для финского языка',
            'language': 'fi',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/hr/cv/vits',
            'name': 'Croatian VITS',
            'description': 'VITS модель для хорватского языка',
            'language': 'hr',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/lt/cv/vits',
            'name': 'Lithuanian VITS',
            'description': 'VITS модель для литовского языка',
            'language': 'lt',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/lv/cv/vits',
            'name': 'Latvian VITS',
            'description': 'VITS модель для латышского языка',
            'language': 'lv',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/mt/cv/vits',
            'name': 'Maltese VITS',
            'description': 'VITS модель для мальтийского языка',
            'language': 'mt',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/pt/cv/vits',
            'name': 'Portuguese VITS',
            'description': 'VITS модель для португальского языка',
            'language': 'pt',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/ro/cv/vits',
            'name': 'Romanian VITS',
            'description': 'VITS модель для румынского языка',
            'language': 'ro',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/sk/cv/vits',
            'name': 'Slovak VITS',
            'description': 'VITS модель для словацкого языка',
            'language': 'sk',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/sl/cv/vits',
            'name': 'Slovenian VITS',
            'description': 'VITS модель для словенского языка',
            'language': 'sl',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/sv/cv/vits',
            'name': 'Swedish VITS',
            'description': 'VITS модель для шведского языка',
            'language': 'sv',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/ca/custom/vits',
            'name': 'Catalan VITS',
            'description': 'VITS модель для каталанского языка, обученная на 101460 высказываниях от 257 спикеров',
            'language': 'ca',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/fa/custom/glow-tts',
            'name': 'Persian Female Glow-TTS',
            'description': 'Персидская GlowTTS модель (женский голос)',
            'language': 'fa',
            'gender': 'female',
            'quality': 'medium',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/bn/custom/vits-male',
            'name': 'Bangla Male VITS',
            'description': 'Бенгальская VITS модель (мужской голос)',
            'language': 'bn',
            'gender': 'male',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/bn/custom/vits-female',
            'name': 'Bangla Female VITS',
            'description': 'Бенгальская VITS модель (женский голос)',
            'language': 'bn',
            'gender': 'female',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/ewe/openbible/vits',
            'name': 'Ewe VITS',
            'description': 'VITS модель для языка эве',
            'language': 'ewe',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/hau/openbible/vits',
            'name': 'Hausa VITS',
            'description': 'VITS модель для языка хауса',
            'language': 'hau',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/lin/openbible/vits',
            'name': 'Lingala VITS',
            'description': 'VITS модель для языка лингала',
            'language': 'lin',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/tw_akuapem/openbible/vits',
            'name': 'Twi Akuapem VITS',
            'description': 'VITS модель для языка тви (акуапем)',
            'language': 'tw_akuapem',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/tw_asante/openbible/vits',
            'name': 'Twi Asante VITS',
            'description': 'VITS модель для языка тви (ашанти)',
            'language': 'tw_asante',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        },
        {
            'id': 'tts_models/yor/openbible/vits',
            'name': 'Yoruba VITS',
            'description': 'VITS модель для языка йоруба',
            'language': 'yor',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False,
            'speakers': False
        }
    ]
}

def get_unique_filename(output_dir: str, filename: str) -> str:
    """Генерирует уникальное имя файла если файл уже существует"""
    base_path = Path(output_dir) / filename
    if not base_path.exists():
        return str(base_path)
    
    # Получаем имя и расширение
    stem = base_path.stem
    suffix = base_path.suffix
    
    # Добавляем случайный UUID
    unique_filename = f'{stem}_{uuid.uuid4().hex[:8]}{suffix}'
    return str(Path(output_dir) / unique_filename)

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница с формой"""
    return templates.TemplateResponse('index.html', {
        'request': request,
        'models': AVAILABLE_MODELS
    })

@app.post('/generate')
async def generate_tts(
    text: str = Form(...),
    model_name: str = Form(...),
    output_filename: str = Form(...),
    speaker_file: UploadFile = File(None),
    language: str = Form(None),
    speaker: str = Form(None)
):
    """API endpoint для генерации TTS"""
    try:
        # Валидация входных данных
        if not text.strip():
            raise HTTPException(status_code=400, detail='Текст не может быть пустым')
        
        if not output_filename.strip():
            raise HTTPException(status_code=400, detail='Имя файла не может быть пустым')
        
        # Проверяем, что модель существует в любой из категорий
        model_exists = False
        for category_models in AVAILABLE_MODELS.values():
            for model in category_models:
                if model['id'] == model_name:
                    model_exists = True
                    break
            if model_exists:
                break
        
        if not model_exists:
            raise HTTPException(status_code=400, detail='Неверная модель')
        
        # Добавляем расширение .wav если его нет
        if not output_filename.endswith('.wav'):
            output_filename += '.wav'
        
        # Генерируем уникальное имя файла
        output_path = get_unique_filename('output', output_filename)
        
        # Обрабатываем загруженный файл образца голоса
        speaker_wav_path = None
        if speaker_file and speaker_file.filename:
            # Проверяем расширение файла
            allowed_extensions = ['.wav', '.mp3', '.flac', '.m4a']
            file_ext = Path(speaker_file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f'Неподдерживаемый формат файла. Разрешены: {", ".join(allowed_extensions)}'
                )
            
            # Сохраняем загруженный файл
            speaker_filename = f'speaker_{uuid.uuid4().hex[:8]}{file_ext}'
            speaker_wav_path = UPLOAD_DIR / speaker_filename
            
            with open(speaker_wav_path, 'wb') as f:
                content = await speaker_file.read()
                f.write(content)
            
            print(f"📁 Speaker file saved: {speaker_wav_path}")
        
        # Генерируем аудио
        generate_audio(
            text=text,
            model_name=model_name,
            output_path=output_path,
            gpu=True,
            speaker_wav=str(speaker_wav_path) if speaker_wav_path else None,
            language=language,
            speaker=speaker
        )
        
        # Удаляем временный файл образца голоса после использования
        if speaker_wav_path and speaker_wav_path.exists():
            try:
                speaker_wav_path.unlink()
                print(f"🗑️ Cleaned up speaker file: {speaker_wav_path}")
            except:
                pass
        
        return {
            'success': True,
            'message': f'Аудио успешно сгенерировано: {os.path.basename(output_path)}',
            'filename': os.path.basename(output_path)
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Full error traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f'Ошибка генерации: {str(e)}')

@app.get('/models')
async def get_models():
    """Получить список доступных моделей"""
    return {'models': AVAILABLE_MODELS}

@app.get('/test/{model_name}')
async def test_model(model_name: str):
    """Тестовый endpoint для проверки работы модели"""
    try:
        from services.tts import generate_audio
        import tempfile
        import os
        
        # Создаем временный файл для теста
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Тестируем с коротким текстом
            generate_audio(
                text="Hello, this is a test.",
                model_name=model_name,
                output_path=temp_path,
                gpu=False,  # Используем CPU для теста
                language="en" if 'multilingual' in model_name else None
            )
            
            # Проверяем, что файл создан
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                return {
                    'success': True,
                    'message': f'Model {model_name} works correctly',
                    'file_size': os.path.getsize(temp_path)
                }
            else:
                return {
                    'success': False,
                    'message': 'Model loaded but no audio generated'
                }
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Error testing model: {str(e)}',
            'traceback': traceback.format_exc()
        }

@app.get('/speakers/{model_name}')
async def get_speakers(model_name: str):
    """Получить список доступных спикеров для модели"""
    try:
        from services.tts import TTS, auto_accept_license, restore_stdin
        
        # Автоматически принимаем лицензию для XTTS v2
        original_stdin = None
        if 'xtts' in model_name.lower():
            original_stdin = auto_accept_license()
        
        try:
            tts = TTS(model_name)
            tts.to('cpu')  # Используем CPU для быстрого получения списка
            
            # Проверяем, есть ли у модели спикеры
            speakers = []
            try:
                if hasattr(tts, 'speakers') and tts.speakers:
                    speakers = list(tts.speakers)
            except:
                pass
                
            return {
                'model_name': model_name,
                'speakers': speakers,
                'has_speakers': len(speakers) > 0
            }
        finally:
            if original_stdin:
                restore_stdin(original_stdin)
                
    except Exception as e:
        return {
            'model_name': model_name,
            'speakers': [],
            'has_speakers': False,
            'error': str(e)
        }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
