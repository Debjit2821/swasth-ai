from groq import Groq

client = Groq(
    api_key="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"
)

def summarize_report(report):

    prompt = f"""
    Explain this medical report in simple language
    understandable by normal rural patients.

    Report:
    {report}
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