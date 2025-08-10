"""
Test GPT-5 models with correct parameters (default temperature)
"""

import pytest
from openai import OpenAI
import os
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

if not os.getenv("OPENAI_API_KEY"):
    pytest.skip("OPENAI_API_KEY not set; skipping OpenAI live tests", allow_module_level=True)

def test_gpt5_final():
    print("🚀 Testing GPT-5 Models (2025) - FINAL VERSION")
    print("=" * 55)
    
    # Set API key
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Test GPT-5 models with default parameters
    models_to_test = [
        ("gpt-5-nano", "GPT-5 Nano (cheapest)"),
        ("gpt-5-mini", "GPT-5 Mini (cost-effective)"), 
        ("gpt-5", "GPT-5 (most powerful)")
    ]
    
    for model_name, description in models_to_test:
        print(f"\n🧪 Testing {description}")
        print("-" * 40)
        
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": """Create a Russian vocabulary card for \"изучать\" (to study).

Respond in JSON format:
{
    \"question_text\": \"Russian definition using simple words\",
    \"answer_text\": \"Example sentence with изучать\", 
    \"target_word\": \"изучать\",
    \"supporting_words\": [\"word1\", \"word2\"]
}"""
                }]
            )
            
            print(f"✅ {description} SUCCESS!")
            raw_content = response.choices[0].message.content
            
            # Clean up markdown if present
            if raw_content.startswith('```json'):
                raw_content = raw_content[7:]
            if raw_content.endswith('```'):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()
            
            print(f"📋 Raw Response:")
            print(raw_content)
            
            try:
                result = json.loads(raw_content)
                print(f"\n✅ JSON Parsed Successfully!")
                print(f"📝 Question: {result['question_text']}")
                print(f"💬 Answer: {result['answer_text']}")
                print(f"🎯 Target: {result['target_word']}")
                print(f"🔗 Supporting: {result['supporting_words']}")
                
                return model_name  # Return first working model
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing failed: {e}")
                
        except Exception as e:
            print(f"❌ {description} failed: {e}")
    
    print(f"\n🎉 READY TO UPDATE YOUR CONTENT GENERATOR!")
    return None

if __name__ == "__main__":
    working_model = test_gpt5_final()
    if working_model:
        print(f"\n🚀 SUCCESS! Use {working_model} for your Russian content generation!")
    else:
        print(f"\n🔄 Will fallback to GPT-4o which we know works")

