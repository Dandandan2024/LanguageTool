#!/usr/bin/env python3
"""
Test script for the lexeme-based API
"""
import requests
import json
import time

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing lexeme-based API...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test 2: Get user profile (should create new user)
    try:
        response = requests.get(f"{base_url}/v1/user/test_lexeme_user", timeout=10)
        print(f"✅ User profile: {response.status_code}")
        user_data = response.json()
        print(f"   User CEFR: {user_data.get('cefr_level')}")
        print(f"   Has placement: {user_data.get('has_placement')}")
    except Exception as e:
        print(f"❌ User profile failed: {e}")
        return
    
    # Test 3: Get session cards (should generate from lexemes)
    try:
        print("\n🎯 Requesting cards from lexeme system...")
        payload = {
            "count": 3,
            "username": "test_lexeme_user"
        }
        response = requests.post(f"{base_url}/v1/sessions/next", 
                               json=payload, timeout=30)
        print(f"✅ Sessions/next: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   User CEFR: {data.get('user_cefr')}")
            print(f"   Cards returned: {len(data.get('items', []))}")
            print(f"   Session breakdown: {data.get('session_breakdown')}")
            
            # Show sample cards
            items = data.get('items', [])
            for i, item in enumerate(items[:2]):  # Show first 2 cards
                print(f"\n   Card {i+1}:")
                print(f"     Type: {item.get('type')}")
                print(f"     ID: {item.get('card_id')}")
                
                payload = item.get('payload', {})
                if isinstance(payload, str):
                    payload = json.loads(payload)
                
                if item.get('type') == 'vocabulary':
                    print(f"     Word: {payload.get('word')}")
                    print(f"     Translation: {payload.get('translation')}")
                elif item.get('type') == 'cloze':
                    print(f"     Text: {payload.get('text')}")
                    print(f"     Answer: {payload.get('answer')}")
                
                print(f"     CEFR: {payload.get('cefr_level')}")
                print(f"     Generation: {payload.get('generation_method')}")
        else:
            print(f"   Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Sessions/next failed: {e}")
        return
    
    print("\n🎉 Lexeme-based API test complete!")

if __name__ == "__main__":
    # Wait a moment for server to start
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    test_api()
