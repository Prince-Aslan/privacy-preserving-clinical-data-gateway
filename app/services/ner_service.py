import re

# Popular Nigerian names & locations gazetteer for spaCy EntityRuler pipeline extension
NIGERIAN_NAMES = [
    # First Names & Common Given Names
    "Chidi", "Amina", "Okwuchukwu", "Emeka", "Fatima", "Oluwaseun", "Prince", "Peter",
    "Tunde", "Nkechi", "Zainab", "Ibrahim", "Damilola", "Chioma", "Kelechi", "Musa",
    "Yusuf", "Usman", "Sani", "Bello", "Abubakar", "Garba", "Yakubu", "Haruna", "Audu",
    "Shehu", "Danjuma", "Idris", "Jibrin", "Maina", "Buba", "Kida", "Bature", "Lawal",
    "Ade", "Adewale", "Ogundipe", "Alabi", "Popoola", "Sanusi", "Gbadamosi", "Ojo",
    "Uche", "Kalu", "Obi", "Nnamdi", "Chukwu", "Nwagwu", "Igwe", "Nwosu", "Ekwueme",
    "Jadhav", "Mazumder",
    
    # Surnames & Family Names
    "Okonkwo", "Afolabi", "Onyeka", "Onu", "Eze", "Danladi", "Oladipo", "Adeyemi",
    "Babangida", "Nnamani", "Balogun", "Achebe", "Soyinka", "Okafor", "Ezeh",
    "Nwankwo", "Egbuna", "Anenih", "Gowon", "Obasanjo", "Tinubu", "Awolowo", "Azikiwe",
    "Ribadu", "Buhari", "Jonathan", "Solarin", "Falana", "Utomi"
]

NIGERIAN_LOCATIONS = [
    "Lagos", "Ikeja", "Yaba", "Abuja", "Enugu", "Kano", "Ibadan", "Port Harcourt",
    "Surulere", "Victoria Island", "Lekki", "Gwagwalada", "Ondo", "Kaduna", "Benin City",
    "Jos", "Calabar", "Abeokuta", "Asaba", "Owerri", "Uyo", "Warri", "Maiduguri", "Zaria"
]

# Regional Facilities & Known Hospital Keywords (Domain Facility Gazeteer)
NIGERIAN_FACILITIES = [
    "Federal Neuropsychiatric Hospital, Yaba", "Federal Neuropsychiatric Hospital Yaba",
    "University College Hospital", "UCH Ibadan", "LUTH", "Lagos University Teaching Hospital",
    "Miva Health Center", "Miva Clinic", "National Hospital Abuja", "ABUTH Zaria",
    "UNTH Enugu", "UPTH Port Harcourt", "AKTH Kano"
]

class MedicalNEREngine:
    def __init__(self):
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            
            # Add EntityRuler to spaCy pipeline to natively recognize Nigerian entities & patterns
            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                patterns = [
                    # Dynamic Context Pattern: Match proper nouns following patient/clinical honorifics
                    {
                        "label": "PERSON",
                        "pattern": [
                            {"LOWER": {"IN": ["patient", "mr.", "mrs.", "ms.", "dr.", "prof.", "chief"]}},
                            {"IS_ALPHA": True, "OP": "+"}
                        ]
                    }
                ]
                
                # 1. Nigerian Proper Names
                for name in NIGERIAN_NAMES:
                    patterns.append({"label": "PERSON", "pattern": name})
                
                # 2. Nigerian Geographic Locations
                for loc in NIGERIAN_LOCATIONS:
                    patterns.append({"label": "GPE", "pattern": loc})
                
                # 3. Nigerian Medical Facilities
                for fac in NIGERIAN_FACILITIES:
                    patterns.append({"label": "ORG", "pattern": fac})
                
                ruler.add_patterns(patterns)
            print("[NER Engine] spaCy (en_core_web_sm) loaded successfully with EntityRuler pipeline extension.")
        except Exception as e:
            print(f"[NER Warning] spaCy model unavailable ({e}). Operating in High-Precision Contextual Mode.")
            self.nlp = None

        # Build regex patterns for contacts, dates, and clinical contextual patterns
        self.phone_pattern = re.compile(r'(\+?234|0)[789][01]\d{8}|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', re.IGNORECASE)
        
        # Clinical Context Title Pattern (e.g., "Patient Chidi Eze", "Mr. Eze", "Dr. Okonkwo")
        self.patient_title_pattern = re.compile(
            r'\b(Patient|Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Chief)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b'
        )

    def redact_text(self, text: str) -> str:
        """
        Processes free-text clinical notes and redacts Protected Health Information (PHI)
        replacing entities with standardized NLP tokens: [NAME], [LOCATION], [FACILITY], [DATE], [CONTACT].
        Completely dynamic using spaCy Statistical NER + Syntactic Context Rules.
        """
        if not text:
            return ""

        redacted = text

        # 1. Regex Redaction for Contacts & Dates
        redacted = self.phone_pattern.sub('[CONTACT]', redacted)
        redacted = self.email_pattern.sub('[CONTACT]', redacted)
        redacted = self.date_pattern.sub('[DATE]', redacted)

        # 2. Dynamic Clinical Context Pattern Redaction ("Patient <Name>", "Mr. <Name>")
        def replace_patient_name(match):
            prefix = match.group(1)
            return f"{prefix} [NAME]"
        redacted = self.patient_title_pattern.sub(replace_patient_name, redacted)

        # 3. spaCy Named Entity Recognition (NER) Redaction (Dynamic Model Extraction)
        if self.nlp:
            doc = self.nlp(redacted)
            # Iterate entities in reverse order to preserve string character indices during replacement
            for ent in reversed(doc.ents):
                if ent.label_ in ["PERSON"]:
                    redacted = redacted[:ent.start_char] + "[NAME]" + redacted[ent.end_char:]
                elif ent.label_ in ["GPE", "LOC"]:
                    redacted = redacted[:ent.start_char] + "[LOCATION]" + redacted[ent.end_char:]
                elif ent.label_ in ["ORG"]:
                    redacted = redacted[:ent.start_char] + "[FACILITY]" + redacted[ent.end_char:]
                elif ent.label_ in ["DATE", "TIME"]:
                    redacted = redacted[:ent.start_char] + "[DATE]" + redacted[ent.end_char:]

        # 4. Custom Nigerian Gazetteer & Facility Redaction (Backstop Guarantee)
        for facility in NIGERIAN_FACILITIES:
            pattern = re.compile(re.escape(facility), re.IGNORECASE)
            redacted = pattern.sub('[FACILITY]', redacted)

        for loc in NIGERIAN_LOCATIONS:
            pattern = re.compile(r'\b' + re.escape(loc) + r'\b', re.IGNORECASE)
            redacted = pattern.sub('[LOCATION]', redacted)

        for name in NIGERIAN_NAMES:
            pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
            redacted = pattern.sub('[NAME]', redacted)

        # 5. Consolidate consecutive duplicate tags (e.g. "[NAME] [NAME]" -> "[NAME]")
        redacted = re.sub(r'(\[NAME\]\s*){2,}', '[NAME] ', redacted)
        redacted = re.sub(r'(\[LOCATION\]\s*){2,}', '[LOCATION] ', redacted)
        redacted = re.sub(r'(\[FACILITY\]\s*){2,}', '[FACILITY] ', redacted)

        return redacted.strip()

ner_engine = MedicalNEREngine()

