# TTS Gen UI

Веб-интерфейс для генерации речи из текста с помощью Coqui TTS.

## Установка

Используйте `Python 3.11+`:
```sh
pip install -r requirements.txt
```

Для CUDA установите:
```sh
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install git+https://github.com/coqui-ai/TTS.git@dev
```

## Запуск

```sh
python app.py
```

Откройте http://localhost:8000 в браузере.

## Возможности

- Выбор модели TTS из списка
- Ввод текста для генерации
- Указание имени выходного файла
- Автоматическое избежание перезаписи файлов
- Минималистичный веб-интерфейс на Tailwind CSS