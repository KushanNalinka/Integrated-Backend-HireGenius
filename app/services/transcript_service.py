import pytesseract
from pdf2image import convert_from_path
import re
import os

# Set paths
# We need to set the path for Tesseract and Poppler in Ubuntu
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
poppler_path = r"C:\Program Files\poppler-20.12.1\Library\bin"

# Define grading system
MARK_ALLOCATION = {
    "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0, "D-":0.7, "F": 0.0
}

# Define job dictionary
JOB_DICTIONARY = {
    "Undergraduate Trainee": [
        "Fundamentals of Programming", "Data Structures and Algorithms", "Version Control (Git)",
        "Basic Database Concepts", "Debugging Techniques", "Software Development Lifecycle"
    ],
    "Associate Software Engineer": [
        "Fundamentals of Programming", "Data Structures and Algorithms", "Software Development Lifecycle",
        "Database Systems", "Software Testing", "Object Oriented Programming", "Cloud Computing Basics"
    ],
    "Software Engineer": [
        "Fundamentals of Programming", "Data Structures and Algorithms", "Software Development Lifecycle",
        "Database Systems", "Software Testing and Quality", "Cloud Computing", "Artificial Intelligence"
    ],
    "Senior Software Engineer": [
        "Software Architecture", "Scalability and Performance Optimization", "Database Optimization",
        "Cloud Computing", "Microservices", "System Design", "Security Best Practices"
    ],
    "Associate Tech Lead": [
        "Software Design Patterns", "System Design", "Code Optimization", "DevOps Principles",
        "Team Mentoring", "Scalability and Reliability", "Security Best Practices"
    ],
    "Tech Lead": [
        "Software Architecture", "Team Leadership", "CI/CD and DevOps", "Cloud Infrastructure",
        "Security and Compliance", "Performance Optimization", "Cross-Team Collaboration"
    ],
    "Senior Lead Software Engineer": [
        "Enterprise Architecture", "Strategic Technology Planning", "Cross-Functional Leadership",
        "System Scalability", "Cloud Security", "Microservices and API Management"
    ],
    "Associate Architect": [
        "System Architecture", "Software Design Patterns", "Scalability and Reliability",
        "Cloud and Infrastructure Design", "Security and Compliance", "Enterprise Software Development"
    ],
    "Architect": [
        "Enterprise Architecture", "System Scalability", "Cloud and Hybrid Architectures",
        "Security Best Practices", "Microservices and Containerization", "Technical Decision Making"
    ],
    "Senior Architect": [
        "Enterprise-Wide Architecture Strategy", "Cloud Transformation", "Security Governance",
        "Large-Scale System Design", "AI and Big Data Architectures", "Technical Leadership"
    ],
    "Backend Developer": [
        "Fundamentals of Programming", "Data Structures and Algorithms", "Database Systems",
        "Software Architecture", "Microservices", "API Development", "Scalability and Performance Optimization"
    ],
    "Frontend Developer": [
        "HTML, CSS, and JavaScript", "Web Frameworks (React, Angular, Vue)", "Responsive Design",
        "User Experience (UX) Design", "Web Performance Optimization", "Browser Rendering and Debugging"
    ],
    "Full Stack Developer": [
        "Fundamentals of Programming", "Data Structures and Algorithms", "Frontend Development",
        "Backend Development", "Database Management", "DevOps and CI/CD", "Cloud Computing"
    ],
    "DevOps Engineer": [
        "Linux Administration", "Cloud Computing", "CI/CD Pipelines", "Infrastructure as Code",
        "Containerization (Docker, Kubernetes)", "Monitoring and Logging", "Security Best Practices"
    ],
    "Data Engineer": [
        "Database Systems", "Big Data Technologies", "ETL Processes", "Cloud Data Platforms",
        "Data Warehousing", "Data Modeling", "Distributed Computing"
    ],
    "Machine Learning Engineer": [
        "Mathematics for Machine Learning", "Probability and Statistics", "Deep Learning",
        "Natural Language Processing", "Data Preprocessing", "Model Deployment", "AI Ethics"
    ],
    "Software Architect": [
        "Software Design Patterns", "System Design", "Scalability and Performance",
        "Cloud Computing", "Enterprise Architecture", "Security Best Practices"
    ],
    "Embedded Systems Engineer": [
        "Microcontrollers and Microprocessors", "Real-Time Operating Systems", "C/C++ Programming",
        "Embedded Linux", "Hardware-Software Integration", "Signal Processing"
    ],
    "Game Developer": [
        "Game Physics", "3D Rendering", "Game Engines (Unity, Unreal)", "AI for Games",
        "Graphics Programming", "Multiplayer Networking"
    ],
    "Mobile Developer": [
        "Android Development (Java/Kotlin)", "iOS Development (Swift)", "Mobile UI/UX",
        "Cross-Platform Development (Flutter, React Native)", "Mobile Security", "App Performance Optimization"
    ],
    "Security Engineer": [
        "Cyber Security", "Penetration Testing", "Network Security", "Application Security",
        "Ethical Hacking", "Secure Software Development"
    ],
    "Cloud Engineer": [
        "Cloud Platforms (AWS, Azure, GCP)", "Infrastructure as Code", "Serverless Computing",
        "Cloud Security", "Networking in Cloud", "Containerization and Orchestration"
    ],
    "Site Reliability Engineer (SRE)": [
        "System Reliability", "Incident Management", "Monitoring and Logging",
        "Infrastructure Automation", "Performance Tuning", "CI/CD Pipelines"
    ]
}


def process_pdf(pdf_path, job_role):
    try:
        pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
        text = "\n".join([pytesseract.image_to_string(page, lang='eng') for page in pages])
    except Exception as e:
        return f"Error processing PDF: {str(e)}"
    
    print("=====Tessaract Extracted Data===>")
    print(text)
    courses = extract_courses(text)
    return calculate_transcript_score(courses, job_role)

def extract_courses(text):
    pattern = r"(\w{2,4}\d{3,4})\s+([\w\s]+)\s+(\d+)\s+([A-F][+-]?)"
    matches = re.findall(pattern, text)
    return {match[1]: match[3] for match in matches}

def calculate_transcript_score(courses, job_role):
    required_courses = JOB_DICTIONARY[job_role]
    total_marks = 0
    completed_courses = 0

    
    for course in required_courses:
        if course in courses:
            grade = courses[course]
            if grade in MARK_ALLOCATION:
                total_marks += MARK_ALLOCATION[grade]
                completed_courses += 1

    if completed_courses == 0:
        return 0  # No relevant courses completed

    max_possible_marks = len(required_courses) * 4  # Max possible if all were A+
    final_score = (total_marks / max_possible_marks) * 100

    return round(final_score, 2)
