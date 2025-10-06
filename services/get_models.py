from TTS.api import TTS

tts = TTS()
print('# Models')
for i, m in enumerate(tts.list_models().list_tts_models()):
    if i != 0:
        print('-----------------------------')
    print(f'### {m}')
    print(tts.list_models().model_info_by_full_name(m))
    print()
