import os
import uuid
from pathlib import Path
from typing import List

# Настройка папки для кэша моделей TTS
MODELS_DIR = Path(__file__).parent / 'models'
MODELS_DIR.mkdir(exist_ok=True)
os.environ['TTS_HOME'] = str(MODELS_DIR)

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
            'id': 'tts_models/multilingual/multi-dataset/your_tts',
            'name': 'YourTTS Multilingual',
            'description': 'Многоязычная модель с клонированием голоса, поддерживает множество языков',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': True
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/xtts_v2',
            'name': 'XTTS v2 Multilingual',
            'description': 'Продвинутая многоязычная модель с клонированием голоса',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': True
        },
        {
            'id': 'tts_models/multilingual/multi-dataset/bark',
            'name': 'Bark Multilingual',
            'description': 'Современная многоязычная модель с эмоциями и клонированием голоса',
            'language': 'multilingual',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': True
        }
    ],
    '🇺🇸 Английские модели': [
        {
            'id': 'tts_models/en/ljspeech/tacotron2-DDC',
            'name': 'LJSpeech Tacotron2-DDC',
            'description': 'Высококачественная английская речь, четкое произношение',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False
        },
        {
            'id': 'tts_models/en/ljspeech/fast_pitch',
            'name': 'LJSpeech FastPitch',
            'description': 'Быстрая генерация английской речи',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'medium',
            'voice_cloning': False
        },
        {
            'id': 'tts_models/en/ljspeech/glow-tts',
            'name': 'LJSpeech Glow-TTS',
            'description': 'Высококачественная английская речь с контролем темпа',
            'language': 'en',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False
        }
    ],
    '🇩🇪 Немецкие модели': [
        {
            'id': 'tts_models/de/thorsten/tacotron2-DDC',
            'name': 'Thorsten Tacotron2-DDC',
            'description': 'Высококачественная немецкая речь',
            'language': 'de',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False
        }
    ],
    '🇫🇷 Французские модели': [
        {
            'id': 'tts_models/fr/mai/tacotron2-DDC',
            'name': 'MAI French Tacotron2-DDC',
            'description': 'Высококачественная французская речь',
            'language': 'fr',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False
        }
    ],
    '🇪🇸 Испанские модели': [
        {
            'id': 'tts_models/es/mai/tacotron2-DDC',
            'name': 'MAI Spanish Tacotron2-DDC',
            'description': 'Высококачественная испанская речь',
            'language': 'es',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False
        }
    ],
    '🇮🇹 Итальянские модели': [
        {
            'id': 'tts_models/it/mai_female/glow-tts',
            'name': 'MAI Italian Female Glow-TTS',
            'description': 'Высококачественная итальянская женская речь',
            'language': 'it',
            'gender': 'female',
            'quality': 'high',
            'voice_cloning': False
        },
        {
            'id': 'tts_models/it/mai_male/glow-tts',
            'name': 'MAI Italian Male Glow-TTS',
            'description': 'Высококачественная итальянская мужская речь',
            'language': 'it',
            'gender': 'male',
            'quality': 'high',
            'voice_cloning': False
        }
    ],
    '🇯🇵 Японские модели': [
        {
            'id': 'tts_models/ja/kokoro/tacotron2-DDC',
            'name': 'Japanese Kokoro Tacotron2-DDC',
            'description': 'Высококачественная японская речь',
            'language': 'ja',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False
        }
    ],
    '🇨🇳 Китайские модели': [
        {
            'id': 'tts_models/zh-CN/baker/tacotron2-DDC-GST',
            'name': 'Chinese Baker Tacotron2-DDC-GST',
            'description': 'Высококачественная китайская речь',
            'language': 'zh',
            'gender': 'mixed',
            'quality': 'high',
            'voice_cloning': False
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
    language: str = Form(None)
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
            language=language
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
        raise HTTPException(status_code=500, detail=f'Ошибка генерации: {str(e)}')

@app.get('/models')
async def get_models():
    """Получить список доступных моделей"""
    return {'models': AVAILABLE_MODELS}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
