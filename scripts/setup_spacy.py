import sys
import subprocess

def download_spacy_model():
    print("[INFO] Downloading spaCy model 'en_core_web_sm'...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("[SUCCESS] spaCy model 'en_core_web_sm' downloaded successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to download spaCy model: {e}")

if __name__ == "__main__":
    download_spacy_model()
