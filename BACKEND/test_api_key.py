import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_api():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    print("Testing google-generativeai for embedding-001...")
    try:
        result = genai.embed_content(
            model="models/embedding-001",
            content="Hello world",
            task_type="retrieval_document",
        )
        print(f"Success! Vector length: {len(result['embedding'])}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
