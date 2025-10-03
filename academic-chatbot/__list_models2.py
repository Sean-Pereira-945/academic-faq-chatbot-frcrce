import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.environ['GEMINI_API_KEY']
genai.configure(api_key=api_key)
models = list(genai.list_models())
print('total models', len(models))
for model in models:
    if 'generateContent' in model.supported_generation_methods:
        print(model.name)
