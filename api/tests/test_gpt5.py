"""
Test GPT-5 (2025) with the latest OpenAI library
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

def test_gpt5_models():
    print("🚀 Testing GPT-5 Models (2025)")
    print("=" * 50)
    
    try:
        # Initialize client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ OpenAI client initialized")
        
        # Test different GPT-5 variants
        models_to_test = [
            ("gpt-5-nano", "GPT-5 Nano (cheapest)"),
            ("gpt-5-mini", "GPT-5 Mini (cost-effective)"), 
            ("gpt-5", "GPT-5 (most powerful)")
        ]
        
        for model_name, description in models_to_test:
            print(f"\n🧪 Testing {description}")
            print("-" * 30)
            
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{
                        "role": "user", 
                        "content": """Create a Russian vocabulary card for "изучать". 
                        
Respond in JSON format:
{
    "question_text": "Russian definition using simple words",
    "answer_text": "Example sentence with изучать",
    "target_word": "изучать",
    "supporting_words": ["word1", "word2"]
}"""
                    }],
                    max_tokens=300,
                    temperature=0.7
                )
                
                print(f"✅ {description} response received!")
                raw_content = response.choices[0].message.content
                
                # Clean up markdown if present
                if raw_content.startswith('```json'):
                    raw_content = raw_content[7:]
                if raw_content.endswith('```'):
                    raw_content = raw_content[:-3]
                raw_content = raw_content.strip()
                
                import json
                result = json.loads(raw_content)
                
                print(f"📝 Question: {result['question_text']}")
                print(f"💬 Answer: {result['answer_text']}")
                print(f"🎯 Target: {result['target_word']}")
                print(f"🔗 Supporting: {result['supporting_words']}")
                
            except Exception as e:
                print(f"❌ {description} failed: {e}")
                
                # If model doesn't exist, try fallback
                if "does not exist" in str(e).lower():
                    print(f"⚠️  {model_name} not available, trying fallback...")
                    
                    # Try GPT-4o as fallback
                    try:
                        fallback_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{
                                "role": "user", 
                                "content": """Create a Russian vocabulary card for "изучать". 
                                
Respond in JSON format:
{
    "question_text": "Russian definition using simple words", 
    "answer_text": "Example sentence with изучать",
                    "target_word": "изучать",
                    "supporting_words": ["word1", "word2"]
}"""
                            }],
                            max_tokens=300,
                            temperature=0.7
                        )
                        
                        print("✅ GPT-4o-mini fallback worked!")
                        fallback_content = fallback_response.choices[0].message.content
                        
                        if fallback_content.startswith('```json'):
                            fallback_content = fallback_content[7:]
                        if fallback_content.endswith('```'):
                            fallback_content = fallback_content[:-3]
                        fallback_content = fallback_content.strip()
                        
                        fallback_result = json.loads(fallback_content)
                        print(f"📝 Fallback Question: {fallback_result['question_text']}")
                        print(f"💬 Fallback Answer: {fallback_result['answer_text']}")
                        
                    except Exception as fallback_error:
                        print(f"❌ Fallback also failed: {fallback_error}")
        
        print(f"\n🎯 Recommendation:")
        print(f"Use GPT-5 Mini for cost-effective, high-quality Russian content generation!")
        
    except Exception as e:
        print(f"❌ Overall test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gpt5_models()

