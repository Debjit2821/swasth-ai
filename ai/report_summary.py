from groq import Groq
import os 
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
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