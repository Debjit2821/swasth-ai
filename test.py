import google.generativeai as genai

genai.configure(api_key="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")

for model in genai.list_models():
    print(model.name)