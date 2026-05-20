from groq import Groq

client = Groq(
    api_key="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"
)

# DETECT SPECIALIST

def detect_specialist(symptoms):

    symptoms = symptoms.lower()

    if any(word in symptoms for word in [
        "chest pain",
        "heart",
        "breathing",
        "blood pressure"
    ]):

        return "Cardiologist"

    elif any(word in symptoms for word in [
        "skin",
        "rash",
        "itching",
        "acne"
    ]):

        return "Dermatologist"

    elif any(word in symptoms for word in [
        "stress",
        "anxiety",
        "depression",
        "mental"
    ]):

        return "Psychiatrist"

    elif any(word in symptoms for word in [
        "headache",
        "brain",
        "memory",
        "seizure"
    ]):

        return "Neurologist"

    return "General Physician"


# AI ANALYSIS

def analyze_symptoms(symptoms):

    specialist = detect_specialist(symptoms)

    prompt = f"""
    You are an AI healthcare assistant.

    Keep response:
    - short
    - simple
    - human-friendly
    - under 100 words

    Structure:

    Possible Issue:
    short explanation

    Advice:
    simple advice

    Recommended Specialist:
    {specialist}

    Symptoms:
    {symptoms}
    If symptoms appear severe or life-threatening,
    strongly advise immediate emergency care.
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