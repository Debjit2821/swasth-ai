from groq import Groq

client = Groq(
    api_key="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"
)

def analyze_symptoms(symptoms):

    prompt = f"""
    Analyze these symptoms carefully:

    Symptoms:
    {symptoms}

    Return response in this format:

    Danger Level:
    Possible Issue:
    Recommendation:
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant",
    )

    return chat_completion.choices[0].message.content