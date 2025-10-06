import os
import uuid
from pathlib import Path
from typing import List

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
    'Английские модели': [
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
        }
    ],
    'Русские модели': [
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
        }
    ],
    'Многоязычные модели': [
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
        }
    ],
    'Специализированные модели': [
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
