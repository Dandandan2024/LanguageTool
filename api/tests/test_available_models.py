"""
Test what models are available with your OpenAI API key
"""

import pytest
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Skip this module if no API key is configured
if not os.getenv("OPENAI_API_KEY"):
    pytest.skip("OPENAI_API_KEY not set; skipping OpenAI live tests", allow_module_level=True)

def test_available_models():
    print("🔍 Testing Available OpenAI Models (2025)")
    print("=" * 50)
    
    # Set API key
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    try:
        # List available models
        models = client.models.list()
        
        print("✅ Successfully retrieved model list!")
        print(f"📊 Total models available: {len(models['data'])}")
        
        # Filter for GPT models
        gpt_models = []
        for model in models['data']:
            model_id = model['id']
            if 'gpt' in model_id.lower():
                gpt_models.append(model_id)
        
        print(f"\n🤖 GPT Models Available:")
        gpt_models.sort()
        for model in gpt_models:
            print(f"  - {model}")
        
        # Test some specific models we're interested in
        test_models = [
            "gpt-5",
            "gpt-5-mini", 
            "gpt-5-nano",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
        
        print(f"\n🧪 Testing Specific Models:")
        working_models = []
        
        for model_name in test_models:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{
                        "role": "user",
                        "content": "Say 'Hello' in Russian."
                    }],
                    max_tokens=10,
                    temperature=0.3
                )

                result = (response.choices[0].message.content or "").strip()
                print(f"  ✅ {model_name}: {result}")
                working_models.append(model_name)
                
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg:
                    print(f"  ❌ {model_name}: Model not available")
                elif "insufficient_quota" in error_msg:
                    print(f"  💰 {model_name}: Available but quota exceeded")
                    working_models.append(model_name)
                else:
                    print(f"  ⚠️  {model_name}: {error_msg[:50]}...")
        
        print(f"\n🎯 Recommendation:")
        if "gpt-5" in working_models:
            print("🚀 Use GPT-5 - Latest and most powerful!")
        elif "gpt-5-mini" in working_models:
            print("🚀 Use GPT-5-Mini - Latest and cost-effective!")
        elif "gpt-4o" in working_models:
            print("🚀 Use GPT-4o - Very capable and reliable!")
        elif "gpt-4o-mini" in working_models:
            print("🚀 Use GPT-4o-mini - Good balance of capability and cost!")
        else:
            print("🚀 Use GPT-3.5-turbo - Reliable fallback!")
            
        return working_models
        
    except Exception as e:
        print(f"❌ Failed to retrieve models: {e}")
        return []

if __name__ == "__main__":
    test_available_models()

