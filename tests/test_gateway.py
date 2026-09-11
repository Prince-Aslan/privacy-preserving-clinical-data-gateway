import unittest
from app.security.crypto import crypto_engine
from app.services.ner_service import ner_engine
from app.simulator.generator import generate_synthetic_record

class TestGatewaySecurity(unittest.TestCase):
    def test_aes256_encryption_decryption(self):
        original_name = "Prince Peter Okwuchukwu"
        encrypted = crypto_engine.encrypt_field(original_name)
        self.assertNotEqual(encrypted, original_name)
        decrypted = crypto_engine.decrypt_field(encrypted)
        self.assertEqual(decrypted, original_name)

    def test_sha256_pseudonymization_determinism(self):
        patient_id = "SYN-992-X"
        hash1 = crypto_engine.hash_sha256(patient_id)
        hash2 = crypto_engine.hash_sha256(patient_id)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # Hex SHA-256 length

    def test_spacy_ner_phi_redaction(self):
        raw_note = "Patient Chidi Okonkwo visited Federal Neuropsychiatric Hospital, Yaba in Lagos on 15/04/2026. Contact: +234-803-123-4567."
        redacted = ner_engine.redact_text(raw_note)
        self.assertNotIn("Chidi", redacted)
        self.assertNotIn("Okonkwo", redacted)
        self.assertNotIn("+234-803-123-4567", redacted)
        self.assertIn("[CONTACT]", redacted)

    def test_ner_eze_and_surnames_redaction(self):
        test_cases = [
            "Patient Eze reports severe insomnia and low energy in Yaba, Lagos.",
            "Patient Chidi Eze was consulted yesterday for depression.",
            "Follow-up visit for Kelechi Eze at Miva Clinic.",
            "Patient Danladi visited the clinic in Abuja.",
            "Mr. Oladipo presented with mild depressive disorder."
        ]
        for note in test_cases:
            redacted = ner_engine.redact_text(note)
            self.assertNotIn("Eze", redacted, f"Failed for note: {note} -> Redacted: {redacted}")
            self.assertNotIn("Chidi", redacted, f"Failed for note: {note} -> Redacted: {redacted}")
            self.assertNotIn("Danladi", redacted, f"Failed for note: {note} -> Redacted: {redacted}")
            self.assertNotIn("Oladipo", redacted, f"Failed for note: {note} -> Redacted: {redacted}")
            self.assertIn("[NAME]", redacted, f"Missing [NAME] token for note: {note}")

    def test_synthetic_data_generator(self):
        record = generate_synthetic_record(1)
        self.assertIn("patient_id", record)
        self.assertIn("pii", record)
        self.assertIn("demographics", record)
        self.assertGreaterEqual(len(record["journey_timeline"]), 1)

if __name__ == "__main__":
    unittest.main()
