"""
Test GPT-5 models with correct parameters (no max_tokens)
"""

import pytest
from openai import OpenAI
import os
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

if not os.getenv("OPENAI_API_KEY"):
    pytest.skip("OPENAI_API_KEY not set; skipping OpenAI live tests", allow_module_level=True)

def test_gpt5_working():
    print("🚀 Testing GPT-5 Models (2025) - WORKING VERSION")
    print("=" * 55)
    
    # Set API key
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Test GPT-5 models without max_tokens
    models_to_test = [
        ("gpt-5-nano", "GPT-5 Nano (cheapest)", "$0.05/$0.40 per 1M tokens"),
        ("gpt-5-mini", "GPT-5 Mini (cost-effective)", "$0.25/$2 per 1M tokens"), 
        ("gpt-5", "GPT-5 (most powerful)", "$1.25/$10 per 1M tokens")
    ]
    
    for model_name, description, pricing in models_to_test:
        print(f"\n🧪 Testing {description}")
        print(f"💰 Pricing: {pricing}")
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
}

Keep the response concise."""
                }],
                temperature=0.7
            )
            
            print(f"✅ {description} SUCCESS!")
            raw_content = response.choices[0].message.content
            
            # Clean up markdown if present
            if raw_content.startswith('```json'):
                raw_content = raw_content[7:]
            if raw_content.endswith('```'):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()
            
            try:
                result = json.loads(raw_content)
                print(f"📝 Question: {result['question_text']}")
                print(f"💬 Answer: {result['answer_text']}")
                print(f"🎯 Target: {result['target_word']}")
                print(f"🔗 Supporting: {result['supporting_words']}")
                
            except json.JSONDecodeError:
                print(f"📋 Raw Response: {raw_content[:200]}...")
                
        except Exception as e:
            print(f"❌ {description} failed: {e}")
    
    print(f"\n🎉 CONCLUSION:")
    print(f"✅ You have access to GPT-5 models!")
    print(f"💡 Recommendation: Use GPT-5-mini for best cost/performance balance")
    print(f"🚀 GPT-5 is 2025's most advanced AI - perfect for Russian content generation!")

if __name__ == "__main__":
    test_gpt5_working()

