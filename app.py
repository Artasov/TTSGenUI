import os
import uuid
from pathlib import Path
from typing import List

# Настройка папки для кэша моделей TTS
MODELS_DIR = Path(__file__).parent / 'models'
MODELS_DIR.mkdir(exist_ok=True)
os.environ['TTS_HOME'] = str(MODELS_DIR)

from fastapi import FastAPI, Request, Form, HTTPException
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

# Доступные модели TTS с подробными описаниями
AVAILABLE_MODELS = {
    '🇺🇸 Английские модели': [
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DDC',
            'name': 'LJSpeech Tacotron2-DDC',
            'description': 'Высококачественная английская женская речь, четкое произношение',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/ljspeech/fast_pitch',
            'name': 'LJSpeech FastPitch',
            'description': 'Быстрая генерация английской женской речи',
            'language': 'en',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/en/ljspeech/glow-tts',
            'name': 'LJSpeech Glow-TTS',
            'description': 'Высококачественная английская речь с контролем темпа',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DCA',
            'name': 'LJSpeech Tacotron2-DCA',
            'description': 'Английская речь с улучшенным вниманием',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/ljspeech/speedy_speech',
            'name': 'LJSpeech Speedy Speech',
            'description': 'Очень быстрая генерация английской речи',
            'language': 'en',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DDC_ph',
            'name': 'LJSpeech Tacotron2-DDC-PH',
            'description': 'Английская речь с фонетическим представлением',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/vctk/vits',
            'name': 'VCTK VITS',
            'description': 'Многоязычная модель с различными акцентами английского',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/ek1/tacotron2',
            'name': 'EK1 Tacotron2',
            'description': 'Английская мужская речь, естественное звучание',
            'language': 'en',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/blizzard2013/capacitron-t2-c50',
            'name': 'Blizzard2013 Capacitron',
            'description': 'Профессиональная английская речь для аудиокниг',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/sam/tacotron-DDC',
            'name': 'SAM Tacotron-DDC',
            'description': 'Английская мужская речь, подходит для новостей',
            'language': 'en',
            'gender': 'male',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/en/lessac/tacotron2-DDC',
            'name': 'Lessac Tacotron2-DDC',
            'description': 'Английская речь с акцентом на произношение',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/lessac/fast_pitch',
            'name': 'Lessac FastPitch',
            'description': 'Быстрая английская речь с четким произношением',
            'language': 'en',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/en/lessac/glow-tts',
            'name': 'Lessac Glow-TTS',
            'description': 'Высококачественная английская речь с контролем интонации',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/lessac/speedy_speech',
            'name': 'Lessac Speedy Speech',
            'description': 'Очень быстрая английская речь с четким произношением',
            'language': 'en',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/en/lessac/tacotron2-DCA',
            'name': 'Lessac Tacotron2-DCA',
            'description': 'Английская речь с улучшенным вниманием и произношением',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        }
    ],
    '🇷🇺 Русские модели': [
        {
            'id': 'tts_models/ru/ruslan/tacotron2-DDC',
            'name': 'Руслан Tacotron2-DDC',
            'description': 'Высококачественная русская мужская речь',
            'language': 'ru',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ru/ruslan/fast_pitch',
            'name': 'Руслан FastPitch',
            'description': 'Быстрая генерация русской мужской речи',
            'language': 'ru',
            'gender': 'male',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/ru/ruslan/glow-tts',
            'name': 'Руслан Glow-TTS',
            'description': 'Высококачественная русская мужская речь с контролем темпа',
            'language': 'ru',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ru/ruslan/speedy_speech',
            'name': 'Руслан Speedy Speech',
            'description': 'Очень быстрая генерация русской мужской речи',
            'language': 'ru',
            'gender': 'male',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/ru/ruslan/tacotron2-DCA',
            'name': 'Руслан Tacotron2-DCA',
            'description': 'Русская мужская речь с улучшенным вниманием',
            'language': 'ru',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ru/mai_female/glow-tts',
            'name': 'MAI Female Glow-TTS',
            'description': 'Русская женская речь, естественное звучание',
            'language': 'ru',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ru/mai_male/glow-tts',
            'name': 'MAI Male Glow-TTS',
            'description': 'Русская мужская речь, четкое произношение',
            'language': 'ru',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ru/mai_female/tacotron2-DDC',
            'name': 'MAI Female Tacotron2-DDC',
            'description': 'Высококачественная русская женская речь',
            'language': 'ru',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ru/mai_male/tacotron2-DDC',
            'name': 'MAI Male Tacotron2-DDC',
            'description': 'Высококачественная русская мужская речь',
            'language': 'ru',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ru/mai_female/fast_pitch',
            'name': 'MAI Female FastPitch',
            'description': 'Быстрая генерация русской женской речи',
            'language': 'ru',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/ru/mai_male/fast_pitch',
            'name': 'MAI Male FastPitch',
            'description': 'Быстрая генерация русской мужской речи',
            'language': 'ru',
            'gender': 'male',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/ru/mai_female/speedy_speech',
            'name': 'MAI Female Speedy Speech',
            'description': 'Очень быстрая генерация русской женской речи',
            'language': 'ru',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/ru/mai_male/speedy_speech',
            'name': 'MAI Male Speedy Speech',
            'description': 'Очень быстрая генерация русской мужской речи',
            'language': 'ru',
            'gender': 'male',
            'quality': 'medium'
        }
    ],
    '🌍 Многоязычные модели': [
        {
            'id': 'tts_models/multilingual/multi-dataset/your_tts',
            'name': 'YourTTS Multilingual',
            'description': 'Многоязычная модель, поддерживает множество языков',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/bark',
            'name': 'Bark Multilingual',
            'description': 'Современная многоязычная модель с эмоциями',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/xtts_v2',
            'name': 'XTTS v2 Multilingual',
            'description': 'Продвинутая многоязычная модель с клонированием голоса',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/xtts_v1',
            'name': 'XTTS v1 Multilingual',
            'description': 'Многоязычная модель с поддержкой клонирования голоса',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/your_tts_v2',
            'name': 'YourTTS v2 Multilingual',
            'description': 'Улучшенная многоязычная модель с лучшим качеством',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high'
        }
    ],
    '🇩🇪 Немецкие модели': [
        {
            'id': 'tts_models/de/thorsten/tacotron2-DDC',
            'name': 'Thorsten Tacotron2-DDC',
            'description': 'Высококачественная немецкая мужская речь',
            'language': 'de',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/de/thorsten/fast_pitch',
            'name': 'Thorsten FastPitch',
            'description': 'Быстрая генерация немецкой мужской речи',
            'language': 'de',
            'gender': 'male',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/de/thorsten/glow-tts',
            'name': 'Thorsten Glow-TTS',
            'description': 'Высококачественная немецкая мужская речь с контролем темпа',
            'language': 'de',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/de/thorsten/speedy_speech',
            'name': 'Thorsten Speedy Speech',
            'description': 'Очень быстрая генерация немецкой мужской речи',
            'language': 'de',
            'gender': 'male',
            'quality': 'medium'
        }
    ],
    '🇫🇷 Французские модели': [
        {
            'id': 'tts_models/fr/mai/tacotron2-DDC',
            'name': 'MAI French Tacotron2-DDC',
            'description': 'Высококачественная французская речь',
            'language': 'fr',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/fr/mai/fast_pitch',
            'name': 'MAI French FastPitch',
            'description': 'Быстрая генерация французской речи',
            'language': 'fr',
            'gender': 'mixed',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/fr/mai/glow-tts',
            'name': 'MAI French Glow-TTS',
            'description': 'Высококачественная французская речь с контролем темпа',
            'language': 'fr',
            'gender': 'mixed',
            'quality': 'high'
        }
    ],
    '🇪🇸 Испанские модели': [
        {
            'id': 'tts_models/es/mai/tacotron2-DDC',
            'name': 'MAI Spanish Tacotron2-DDC',
            'description': 'Высококачественная испанская речь',
            'language': 'es',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/es/mai/fast_pitch',
            'name': 'MAI Spanish FastPitch',
            'description': 'Быстрая генерация испанской речи',
            'language': 'es',
            'gender': 'mixed',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/es/mai/glow-tts',
            'name': 'MAI Spanish Glow-TTS',
            'description': 'Высококачественная испанская речь с контролем темпа',
            'language': 'es',
            'gender': 'mixed',
            'quality': 'high'
        }
    ],
    '🇮🇹 Итальянские модели': [
        {
            'id': 'tts_models/it/mai_female/tacotron2-DDC',
            'name': 'MAI Italian Female Tacotron2-DDC',
            'description': 'Высококачественная итальянская женская речь',
            'language': 'it',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/it/mai_male/tacotron2-DDC',
            'name': 'MAI Italian Male Tacotron2-DDC',
            'description': 'Высококачественная итальянская мужская речь',
            'language': 'it',
            'gender': 'male',
            'quality': 'high'
        },
        {
            'id': 'tts_models/it/mai_female/fast_pitch',
            'name': 'MAI Italian Female FastPitch',
            'description': 'Быстрая генерация итальянской женской речи',
            'language': 'it',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/it/mai_male/fast_pitch',
            'name': 'MAI Italian Male FastPitch',
            'description': 'Быстрая генерация итальянской мужской речи',
            'language': 'it',
            'gender': 'male',
            'quality': 'medium'
        }
    ],
    '🇳🇱 Голландские модели': [
        {
            'id': 'tts_models/nl/mai/tacotron2-DDC',
            'name': 'MAI Dutch Tacotron2-DDC',
            'description': 'Высококачественная голландская речь',
            'language': 'nl',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/nl/mai/fast_pitch',
            'name': 'MAI Dutch FastPitch',
            'description': 'Быстрая генерация голландской речи',
            'language': 'nl',
            'gender': 'mixed',
            'quality': 'medium'
        }
    ],
    '🇵🇱 Польские модели': [
        {
            'id': 'tts_models/pl/mai_female/tacotron2-DDC',
            'name': 'MAI Polish Female Tacotron2-DDC',
            'description': 'Высококачественная польская женская речь',
            'language': 'pl',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/pl/mai_male/tacotron2-DDC',
            'name': 'MAI Polish Male Tacotron2-DDC',
            'description': 'Высококачественная польская мужская речь',
            'language': 'pl',
            'gender': 'male',
            'quality': 'high'
        }
    ],
    '🇹🇷 Турецкие модели': [
        {
            'id': 'tts_models/tr/common_voice/tacotron2-DDC',
            'name': 'Turkish Common Voice Tacotron2-DDC',
            'description': 'Высококачественная турецкая речь',
            'language': 'tr',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/tr/common_voice/fast_pitch',
            'name': 'Turkish Common Voice FastPitch',
            'description': 'Быстрая генерация турецкой речи',
            'language': 'tr',
            'gender': 'mixed',
            'quality': 'medium'
        }
    ],
    '🇨🇳 Китайские модели': [
        {
            'id': 'tts_models/zh-CN/baker/tacotron2-DDC',
            'name': 'Chinese Baker Tacotron2-DDC',
            'description': 'Высококачественная китайская речь',
            'language': 'zh',
            'gender': 'mixed',
            'quality': 'high'
        },
        {
            'id': 'tts_models/zh-CN/baker/fast_pitch',
            'name': 'Chinese Baker FastPitch',
            'description': 'Быстрая генерация китайской речи',
            'language': 'zh',
            'gender': 'mixed',
            'quality': 'medium'
        }
    ],
    '🇯🇵 Японские модели': [
        {
            'id': 'tts_models/ja/kokoro/tacotron2-DDC',
            'name': 'Japanese Kokoro Tacotron2-DDC',
            'description': 'Высококачественная японская речь',
            'language': 'ja',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ja/kokoro/fast_pitch',
            'name': 'Japanese Kokoro FastPitch',
            'description': 'Быстрая генерация японской речи',
            'language': 'ja',
            'gender': 'female',
            'quality': 'medium'
        }
    ],
    '🇰🇷 Корейские модели': [
        {
            'id': 'tts_models/ko/kss/tacotron2-DDC',
            'name': 'Korean KSS Tacotron2-DDC',
            'description': 'Высококачественная корейская речь',
            'language': 'ko',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/ko/kss/fast_pitch',
            'name': 'Korean KSS FastPitch',
            'description': 'Быстрая генерация корейской речи',
            'language': 'ko',
            'gender': 'female',
            'quality': 'medium'
        }
    ],
    '⚡ Специализированные модели': [
        {
            'id': 'tts_models/en/ljspeech/speedy_speech',
            'name': 'LJSpeech Speedy Speech',
            'description': 'Очень быстрая генерация английской речи',
            'language': 'en',
            'gender': 'female',
            'quality': 'medium'
        },
        {
            'id': 'tts_models/en/ljspeech/glow-tts',
            'name': 'LJSpeech Glow-TTS',
            'description': 'Высококачественная английская речь с контролем темпа',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DCA',
            'name': 'LJSpeech Tacotron2-DCA',
            'description': 'Английская речь с улучшенным вниманием',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DDC_ph',
            'name': 'LJSpeech Tacotron2-DDC-PH',
            'description': 'Английская речь с фонетическим представлением',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
        },
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DDC_ph_glow',
            'name': 'LJSpeech Tacotron2-DDC-PH-Glow',
            'description': 'Английская речь с фонетикой и контролем темпа',
            'language': 'en',
            'gender': 'female',
            'quality': 'high'
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
    output_filename: str = Form(...)
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
        
        # Генерируем аудио
        generate_audio(
            text=text,
            model_name=model_name,
            output_path=output_path,
            gpu=True
        )
        
        return {
            'success': True,
            'message': f'Аудио успешно сгенерировано: {os.path.basename(output_path)}',
            'filename': os.path.basename(output_path)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Ошибка генерации: {str(e)}')

@app.get('/models')
async def get_models():
    """Получить список доступных моделей"""
    return {'models': AVAILABLE_MODELS}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
