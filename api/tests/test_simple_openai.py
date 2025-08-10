"""
Simple test to see what OpenAI is returning
"""

import pytest
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

if not os.getenv("OPENAI_API_KEY"):
    pytest.skip("OPENAI_API_KEY not set; skipping OpenAI live tests", allow_module_level=True)

def test_simple_openai():
    # Set API key
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    print("🧪 Testing Simple OpenAI Call")
    print("=" * 40)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": "Create a simple Russian vocabulary card for the word 'читать'. Respond in JSON format with keys: question_text, answer_text, target_word."
            }],
            max_tokens=200,
            temperature=0.7
        )
        
        print("✅ OpenAI Response received!")
        print("📋 Raw response:")
        print(response.choices[0].message.content)
        print("\n" + "="*40)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_openai()

