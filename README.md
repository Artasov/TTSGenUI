# TTS Gen UI

Веб-интерфейс для генерации речи из текста с помощью Coqui TTS.

## Установка

Используйте `Python 3.11`:

```shell
python.exe -m pip install --upgrade pip
```

**ВАЖНО**: Сначала установите torch для вашей версии CUDA:
```sh
# Для CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Для CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Для CPU (без CUDA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

Затем установите остальные зависимости:
```sh
pip install -r requirements.txt
pip install git+https://github.com/coqui-ai/TTS.git@dev
```

**Проверенные конфигурации:**
- Nvidia 4070 Super + CUDA 12.9
- Windows 10/11 + Python 3.11

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