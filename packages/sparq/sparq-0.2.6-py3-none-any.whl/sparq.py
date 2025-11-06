from client import Sparq


def _demo_plan():
    """Run a demo plan request. This is for CLI/example usage only and
    must not run on import (so importing `sparq` doesn't trigger network
    calls)."""
    client = Sparq()

    # edit accordingly
    plan = client.plan(
        major= "Computer Science",
        cc_courses= [
        # EVC Courses (based on actual transcript)
        {"code": "COMSC 075", "title": "Computer Science I", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMSC 076", "title": "Computer Science II", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMS 020", "title": "Oral Communication", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "ART 096", "title": "History of Asian Art", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMS 035", "title": "Intercultural Communication", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PSYCH 001", "title": "General Psychology", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PHIL 060", "title": "Logic and Critical Thinking", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PHIL 010", "title": "Introduction to Philosophy", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "PHIL 065", "title": "Introduction to Ethics", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "COMSC 080", "title": "Discrete Structures", "grade": "A", "institution": "Evergreen Valley College"},
        {"code": "HIST 017A", "title": "History of the United States", "grade": "A", "institution": "Evergreen Valley College"},
        # SJCC Courses
        {"code": "ENGL 001A", "title": "English Composition", "grade": "A", "institution": "San Jose City College"},
    ],
    ap_exams= [
        {"test": "Calculus AB", "score": 5},
        {"test": "Calculus BC", "score": 4},
        {"test": "World History", "score": 4},
        {"test": "Physics C, Mechanics", "score": 4},
    ],
    sjsu_courses= [
        {"code": "MATH 32", "title": "Calculus III", "status": "In Progress", "term": "Fall 2025"},
        {"code": "CS 49J", "title": "Programming in Java", "status": "In Progress", "term": "Fall 2025"},
        {"code": "NUFS 16", "title": "Nutrition", "status": "In Progress", "term": "Fall 2025"},
        {"code": "METR 10", "title": "Weather and Climate", "status": "In Progress", "term": "Fall 2025"},
    ],
    units_per_semester= 15
    )

    print(plan)


if __name__ == "__main__":
    _demo_plan()