# test_gemini.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

print("Attempting to initialize Gemini...")

try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    genai.configure(api_key=api_key)

    print("Gemini configured. Creating model...")
    model = genai.GenerativeModel('gemini-1.5-flash')

    print("Model created. Sending a simple test prompt...")
    response = model.generate_content("Tell me a short, one-sentence joke.")

    print("\n--- SUCCESS! ---")
    print(response.text)
    print("--------------------")
    print("If you see this message, your API key and Google Cloud project are set up correctly.")

except Exception as e:
    print("\n--- TEST FAILED ---")
    print(f"An error occurred: {type(e).__name__}")
    print(f"Error Details: {e}")
    print("---------------------")
    print("This confirms the problem is with your API key, billing, or Google Cloud project settings, NOT the Flask application code.")