from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(
   api_key=os.environ.get("GROQ_API_KEY")
)


# DETECT SPECIALIST

def detect_specialist(symptoms):

    symptoms = symptoms.lower()

    # CARDIOLOGY

    if any(word in symptoms for word in [

        "chest pain",
        "heart",
        "breathing",
        "blood pressure",
        "palpitations",
        "shortness of breath"
    ]):

        return "Cardiologist"

    # DERMATOLOGY

    elif any(word in symptoms for word in [

        "skin",
        "rash",
        "itching",
        "acne"
    ]):

        return "Dermatologist"

    # PSYCHIATRY

    elif any(word in symptoms for word in [

        "stress",
        "anxiety",
        "depression",
        "mental",
        "panic"
    ]):

        return "Psychiatrist"

    # NEUROLOGY

    elif any(word in symptoms for word in [

        "headache",
        "brain",
        "memory",
        "seizure",
        "migraine",
        "stroke",
        "numbness",
        "nerve"
    ]):

        return "Neurologist"

    return "General Physician"
# AI ANALYSIS

def analyze_symptoms(symptoms):

    specialist = detect_specialist(symptoms)

        
    prompt = f"""

        You are SWASTH-AI,
        a smart and friendly healthcare assistant.
        
        Your job:
        - analyze symptoms
        - give basic healthcare guidance
        - recommend specialists
        - ask follow-up questions if needed
        
        IMPORTANT RULES:
        
        1. Do NOT reject normal medical symptoms.
        
        2. Symptoms like:
        dizziness,
        fatigue,
        nausea,
        stress,
        anxiety,
        headache,
        weakness,
        mild chest pain,
        body pain,
        fever,
        cough,
        stomach pain
        are valid healthcare discussions.
        
        3. Only warn emergency care for:
        - severe chest pain
        - stroke symptoms
        - unconsciousness
        - seizures
        - severe breathing issues
        - heavy bleeding
        - suicide/self-harm intent
        
        4. If symptoms are unclear or too short,
        ask follow-up questions naturally.
        
        5. Never say:
        "invalid symptom"
        or
        "I cannot help."
        
        6. Keep response:
        - short
        - human-friendly
        - medically helpful
        - under 120 words
        
        Format:
        
        Possible Issue:
        short explanation
        
        Advice:
        simple advice
        
        Recommended Specialist:
        {specialist}
        
        Symptoms:
        {symptoms}

"""

    completion = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    return completion.choices[0].message.content, specialist


# CASE SUMMARY

def generate_case_summary(symptoms):

    prompt = f"""
    Summarize this medical case briefly for a doctor.

    Keep it:
    - professional
    - short
    - medically useful
    - under 80 words

    Symptoms:
    {symptoms}
    """

    completion = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    return completion.choices[0].message.content