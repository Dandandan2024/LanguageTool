"""
Test GPT-4o with the latest OpenAI library
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

def test_gpt4o():
    print("🚀 Testing GPT-4o with Latest OpenAI Library")
    print("=" * 50)
    
    try:
        # Initialize client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("✅ OpenAI client initialized")
        
        # Test GPT-4o-mini (cost-effective, latest)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user", 
                "content": """Create a Russian vocabulary card for "читать". 
                
Respond in JSON format:
{
    "question_text": "Russian definition using simple words",
    "answer_text": "Example sentence with читать",
    "target_word": "читать",
    "supporting_words": ["word1", "word2"]
}"""
            }],
            max_tokens=300,
            temperature=0.7
        )
        
        print("✅ GPT-4o-mini response received!")
        print("📋 Raw response:")
        raw_content = response.choices[0].message.content
        print(raw_content)
        
        # Clean up markdown if present
        if raw_content.startswith('```json'):
            raw_content = raw_content[7:]
        if raw_content.endswith('```'):
            raw_content = raw_content[:-3]
        raw_content = raw_content.strip()
        
        import json
        result = json.loads(raw_content)
        
        print("\n✅ Successfully parsed JSON!")
        print(f"📝 Question: {result['question_text']}")
        print(f"💬 Answer: {result['answer_text']}")
        print(f"🎯 Target: {result['target_word']}")
        print(f"🔗 Supporting: {result['supporting_words']}")
        
        print("\n🎉 GPT-4o-mini is working perfectly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gpt4o()

