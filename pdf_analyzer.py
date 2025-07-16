# pdf_analyzer.py (renamed from resume_analyzer.py for clarity)

import os
import argparse
import json
from datetime import datetime, timezone
import fitz  # PyMuPDF
import google.generativeai as genai # MODIFIED: Import Gemini
from dotenv import load_dotenv

# --- 1. SETUP: LOAD API KEY ---
load_dotenv()

# --- MODIFIED: Gemini Client Initialization ---
model = None
try: 
    # Use the same environment variable as the main app
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("Error: GEMINI_API_KEY not found in .env file.")
    else:
        genai.configure(api_key=gemini_key)
        # Using a more powerful model for high-quality standalone analysis
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("Gemini model 'gemini-1.5-pro' initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
# --- END MODIFICATION ---

# --- PASTE YOUR JOB DESCRIPTION HERE ---
JOB_DESCRIPTION_TEXT = """
--- JOB DESCRIPTION ---
Position: Junior Python Developer (Backend)
Location: Remote
We are seeking a highly skilled Junior Python Developer to join our backend development team.
The ideal candidate will have extensive experience in building robust, scalable, and high-performance
applications. You will be responsible for designing and implementing server-side logic,
managing database interactions, and ensuring seamless integration with front-end services.
Key Responsibilities:
- Design, develop, and maintain efficient, reusable, and reliable Python code.
- Implement security and data protection measures.
- Integrate with various data storage solutions, including SQL (PostgreSQL) and NoSQL (Redis) databases.
- Develop and maintain RESTful APIs and microservices.
- Work with cloud platforms like AWS, particularly services like EC2, S3, and Lambda.
- Utilize containerization technologies such as Docker and orchestration tools like Kubernetes.
- Write unit and integration tests to ensure code quality.
Required Skills & Qualifications:
- 5+ years of professional experience in Python development.
- Strong proficiency with backend frameworks like Django, Flask, or FastAPI.
- Solid understanding of database systems (PostgreSQL preferred).
- Experience with Docker and Kubernetes is a must.
- Proven experience with AWS cloud services.
- Familiarity with CI/CD pipelines.
- Excellent problem-solving skills and ability to work in an agile environment.
"""

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at '{pdf_path}'")
        return None
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

# --- MODIFIED: Gemini AI ANALYSIS FUNCTION ---
def analyze_resume_with_gemini(resume_text, jd_text):
    """
    Sends resume and JD to Gemini for analysis and returns structured JSON.
    """
    if not model:
        print("Gemini model not available. Cannot perform analysis.")
        return None

    print("\n🤖 Sending data to Gemini for analysis...")
    
    generation_config = {
      "temperature": 0.2,
      "response_mime_type": "application/json",
    }
    
    # This detailed prompt instructs the AI to act as a career coach
    # and return a specific JSON structure.
    full_prompt = (
        "You are an expert career coach and resume reviewer. Your task is to analyze a resume "
        "against a job description and provide a detailed, actionable analysis. Your entire output "
        "MUST be a single, valid JSON object, and nothing else.\n\n"
        f"Please analyze the following resume against the provided job description.\n\n"
        f"{jd_text}\n\n"
        f"--- RESUME TEXT ---\n{resume_text}\n\n"
        "--- ANALYSIS INSTRUCTIONS ---\n"
        "Based on the texts above, please generate a JSON object with the following structure:\n"
        '- "match_score": An estimated percentage (0-100) of how well the resume matches the job description.\n'
        '- "summary": A brief, 2-3 sentence overall summary of the candidate\'s fit for the role.\n'
        '- "strengths": A list of key skills and experiences from the resume that directly match the job description\'s requirements.\n'
        '- "missing_keywords": A list of important keywords, technologies, or qualifications from the job description that are missing or not clearly stated in the resume.\n'
        '- "suggested_changes": A list of specific, actionable suggestions for the candidate to improve their resume for this specific job. For example, "Quantify your achievement in Project X by adding metrics..." or "Add a \'Cloud Technologies\' section and mention your AWS experience more prominently."'
    )

    try:
        response = model.generate_content(full_prompt, generation_config=generation_config)
        
        # Access response differently for Gemini
        response_content = response.text
        print("✅ Analysis received from Gemini.")
        return json.loads(response_content)

    except Exception as e:
        print(f"An error occurred with the Gemini API call: {e}")
        return None

# --- MAIN EXECUTION BLOCK (Updated function call) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyzes a resume PDF against a job description using Google Gemini AI."
    )
    parser.add_argument(
        "resume_path", 
        help="The full path to the resume PDF file."
    )
    args = parser.parse_args()

    # Step 1: Extract text from resume
    print(f"📄 Reading resume: {args.resume_path}")
    resume_text = extract_text_from_pdf(args.resume_path)

    if resume_text:
        # Step 2: Perform AI analysis
        analysis_result = analyze_resume_with_gemini(resume_text, JOB_DESCRIPTION_TEXT)

        # Step 3: Print the results
        if analysis_result:
            print("\n" + "="*25 + " RESUME ANALYSIS REPORT " + "="*25)
            
            print(f"\n🎯 Match Score: {analysis_result.get('match_score', 'N/A')}%")
            print(f"\n📝 Summary:\n{analysis_result.get('summary', 'No summary provided.')}")
            
            print("\n👍 Strengths (Matching keywords found):")
            for strength in analysis_result.get('strengths', []):
                print(f"  - {strength}")

            print("\n❌ Missing Keywords & Skills:")
            for missing in analysis_result.get('missing_keywords', []):
                print(f"  - {missing}")

            print("\n💡 Suggested Changes & Improvements:")
            for change in analysis_result.get('suggested_changes', []):
                print(f"  - {change}")
            
            print("\n" + "="*72 + "\n")