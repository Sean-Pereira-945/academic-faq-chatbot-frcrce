import google.generativeai as genai
import os
print('api key exists?', bool(os.getenv('GEMINI_API_KEY')))
models = list(genai.list_models())
print('total models', len(models))
for model in models[:10]:
    print(model.name)
