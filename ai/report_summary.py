from groq import Groq
import os 
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def summarize_report(report):

    summary_prompt = f"""
    You are a medical report simplifier.

    Your job:
    - simplify the doctor's report
    - keep ALL medical meaning EXACTLY SAME
    - NEVER change diagnosis
    - NEVER change medicine names
    - NEVER invent information
    - NEVER assume missing details
    - NEVER modify dosage or instructions

    If the doctor report contains:
    - unclear text
    - gibberish
    - random words
    - incomplete instructions

    then clearly mention:
    "The doctor report contains unclear or incomplete information."

    Create:
    - short
    - patient-friendly
    - medically accurate summary

    Keep under 120 words.


    Report:
    {report}
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": summary_prompt,
            }
        ],
        model="llama-3.1-8b-instant",
    )

    return chat_completion.choices[0].message.content