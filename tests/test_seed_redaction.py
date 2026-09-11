import unittest
from app.simulator.generator import generate_synthetic_dataset, LAST_NAMES, FIRST_NAMES
from app.services.ner_service import ner_engine
from app.pipeline.dagster_pipeline import run_pipeline_manually
from app.services.db_service import db_service

class TestSyntheticSeedRedaction(unittest.TestCase):
    def test_all_generated_names_redacted(self):
        records = generate_synthetic_dataset(100)
        unmasked_occurrences = []

        for r in records:
            for visit in r["journey_timeline"]:
                raw_note = visit["clinical_notes"]
                scrubbed = ner_engine.redact_text(raw_note)

                # Verify no raw name from FIRST_NAMES or LAST_NAMES appears unmasked in scrubbed note
                for fn in FIRST_NAMES:
                    if fn in scrubbed:
                        unmasked_occurrences.append((fn, raw_note, scrubbed))
                for ln in LAST_NAMES:
                    if ln in scrubbed:
                        unmasked_occurrences.append((ln, raw_note, scrubbed))

        self.assertEqual(len(unmasked_occurrences), 0, f"Found unmasked names: {unmasked_occurrences[:5]}")

    def test_pipeline_seeding_counts(self):
        seeded_patients = 50
        vault_cnt, analytics_cnt = run_pipeline_manually(seeded_patients)

        self.assertGreaterEqual(vault_cnt, seeded_patients)
        self.assertGreaterEqual(analytics_cnt, seeded_patients)

if __name__ == "__main__":
    unittest.main()
