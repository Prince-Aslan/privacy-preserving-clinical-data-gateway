import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

FIRST_NAMES = ["Chidi", "Amina", "Okwuchukwu", "Emeka", "Fatima", "Oluwaseun", "Prince", "Peter", "Tunde", "Nkechi", "Zainab", "Ibrahim", "Damilola", "Chioma", "Kelechi"]
LAST_NAMES = ["Okonkwo", "Afolabi", "Bello", "Ade", "Onyeka", "Onu", "Yusuf", "Eze", "Danladi", "Oladipo"]
GENDERS = ["Male", "Female"]
LOCATIONS = ["Lagos, Nigeria", "Abuja, Nigeria", "Ikeja, Nigeria", "Yaba, Nigeria", "Enugu, Nigeria", "Kano, Nigeria", "Ibadan, Nigeria"]

DIAGNOSES = [
    "Pending Evaluation",
    "Major Depressive Disorder (Mild)",
    "Major Depressive Disorder (Moderate)",
    "Major Depressive Disorder (Severe)",
    "Generalized Anxiety Disorder",
    "Post-Traumatic Stress Disorder",
    "Bipolar Disorder (Type I)",
    "Schizophrenia (In Remission)"
]

MEDICATIONS = [
    {"name": "Sertraline", "dosage": "50mg"},
    {"name": "Fluoxetine", "dosage": "20mg"},
    {"name": "Escitalopram", "dosage": "10mg"},
    {"name": "Olanzapine", "dosage": "5mg"},
    {"name": "Risperidone", "dosage": "2mg"}
]

THERAPIES = [
    {"name": "Cognitive Behavioral Therapy (CBT)"},
    {"name": "Supportive Psychotherapy"},
    {"name": "Mindfulness-Based Stress Reduction"}
]

CLINICAL_NOTE_TEMPLATES = [
    "Patient {name} reports severe insomnia and low energy. Anhedonia is present for past 2 weeks in {location}. Patient consulted traditional healer prior to clinic visit.",
    "Follow-up visit for {name}. Reports improvement in anxiety symptoms after starting CBT at {location} facility. PHQ-9 score trending lower.",
    "Initial psychiatric assessment for {name}, age {age}. Patient expressed feelings of persistent sadness and sleep disturbance. Living in {location}.",
    "Longitudinal follow-up. Patient {name} shows clinical remission under medication regimen. Continues therapy at local clinic in {location}."
]

def generate_synthetic_record(record_index: int) -> Dict[str, Any]:
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    full_name = f"{first_name} {last_name}"
    phone = f"+234-80{random.randint(10,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
    patient_id = f"SYN-{random.randint(100,999)}-{chr(65 + (record_index % 26))}"
    age = random.randint(18, 65)
    gender = random.choice(GENDERS)
    location = random.choice(LOCATIONS)

    # Simulate 1 to 3 longitudinal journey visits
    num_visits = random.randint(1, 3)
    journey_timeline = []
    base_time = datetime.utcnow() - timedelta(days=random.randint(30, 180))

    initial_phq9 = random.randint(12, 24)
    current_phq9 = initial_phq9

    for i in range(num_visits):
        visit_time = base_time + timedelta(days=i * 14)
        if i > 0:
            current_phq9 = max(0, current_phq9 - random.randint(3, 7))

        diagnosis = DIAGNOSES[0] if i == 0 else random.choice(DIAGNOSES[1:])
        note_template = random.choice(CLINICAL_NOTE_TEMPLATES)
        clinical_note = note_template.format(name=full_name, location=location, age=age)

        treatment_plan = []
        if current_phq9 > 10:
            med = random.choice(MEDICATIONS)
            treatment_plan.append({"type": "Medication", "name": med["name"], "dosage": med["dosage"]})
            th = random.choice(THERAPIES)
            treatment_plan.append({"type": "Therapy", "name": th["name"]})
        else:
            treatment_plan.append({"type": "Assessment", "name": "Routine Follow-up"})

        journey_timeline.append({
            "timestamp": visit_time.isoformat() + "Z",
            "phq9_score": current_phq9,
            "clinical_notes": clinical_note,
            "diagnosis": diagnosis,
            "treatment_plan": treatment_plan
        })

    return {
        "patient_id": patient_id,
        "pii": {
            "patient_name": full_name,
            "contact_info": phone
        },
        "demographics": {
            "age": age,
            "gender": gender,
            "location": location
        },
        "journey_timeline": journey_timeline
    }

def generate_synthetic_dataset(num_records: int = 100) -> List[Dict[str, Any]]:
    return [generate_synthetic_record(i) for i in range(num_records)]
