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

# Создаем папку output если её нет
os.makedirs('output', exist_ok=True)

# Доступные модели TTS
AVAILABLE_MODELS = [
    'tts_models/en/ljspeech/tacotron2-DDC',
    'tts_models/en/ljspeech/fast_pitch',
    'tts_models/en/vctk/vits',
    'tts_models/en/ek1/tacotron2',
    'tts_models/multilingual/multi-dataset/your_tts',
    'tts_models/ru/ruslan/tacotron2-DDC',
    'tts_models/ru/ruslan/fast_pitch',
]

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
        
        if model_name not in AVAILABLE_MODELS:
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
