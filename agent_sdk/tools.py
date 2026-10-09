from pathlib import Path 
from agents import function_tool

DATA_DIR = Path(__file__).resolve().parent.parent/"data"

REAL_FILE = DATA_DIR/"resume_facts.json"
DEMO_FILE = DATA_DIR / "resume_facts.demo.json"


def read_resume_facts()->str:
    file_path = REAL_FILE if REAL_FILE.exists() else DEMO_FILE
    return file_path.read_text(encoding="utf-8")

@function_tool
def get_resume_facts() -> str:
    """
    Return the user's resume facts, including skills, projects,
    and work experience.

    These are the only facts allowed when describing the user's
    professional background or drafting job-related messages.

    Never claim skills, projects, qualifications, or experience
    that are not explicitly supported by this result.

    Call this before writing any note or message that describes the user's background.
    """
    
    return read_resume_facts()


    

