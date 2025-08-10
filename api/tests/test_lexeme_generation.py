#!/usr/bin/env python3
"""
Direct test of lexeme-based card generation without running the full API server
"""
import os
import json
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment
load_dotenv(dotenv_path=os.path.join('..', '.env'))

def db_connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

def test_lexeme_generation():
    print("🧪 Testing lexeme-based card generation directly...")
    
    conn = db_connect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Import the generation function from main
            from main import generate_cards_from_lexemes_for_user
            
            # Test parameters
            username = "test_direct_user"
            user_cefr = "A1"
            count = 3
            theta_min = -3.0
            theta_max = -1.0
            
            print(f"📋 Testing with: user={username}, cefr={user_cefr}, count={count}")
            
            # Check lexemes available
            cur.execute("""
                SELECT COUNT(*) as count FROM lexemes 
                WHERE language = 'ru' AND cefr_level = %s
            """, (user_cefr,))
            lexeme_count = cur.fetchone()['count']
            print(f"📚 Available {user_cefr} lexemes: {lexeme_count}")
            
            if lexeme_count == 0:
                print("❌ No lexemes found for testing")
                return
            
            # Test the generation function
            print("🎯 Generating cards...")
            generated_cards = generate_cards_from_lexemes_for_user(
                cur, username, user_cefr, count, theta_min, theta_max
            )
            
            print(f"✅ Generated {len(generated_cards)} cards")
            
            # Show the generated cards
            for i, card in enumerate(generated_cards):
                print(f"\n📄 Card {i+1}:")
                print(f"   ID: {card['card_id']}")
                print(f"   Type: {card['type']}")
                
                payload = card['payload']
                if isinstance(payload, str):
                    payload = json.loads(payload)
                
                if card['type'] == 'vocabulary':
                    print(f"   Word: {payload.get('word')}")
                    print(f"   Translation: {payload.get('translation')}")
                elif card['type'] == 'cloze':
                    print(f"   Text: {payload.get('text')}")
                    print(f"   Answer: {payload.get('answer')}")
                
                print(f"   CEFR: {payload.get('cefr_level')}")
                print(f"   Target Word: {payload.get('target_word')}")
                print(f"   Generation: {payload.get('generation_method')}")
            
            # Verify cards were inserted into database
            cur.execute("SELECT COUNT(*) as count FROM cards WHERE language = 'ru'")
            total_cards = cur.fetchone()['count']
            print(f"\n📊 Total Russian cards in database: {total_cards}")
            
            conn.commit()
            print("\n🎉 Lexeme generation test completed successfully!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_lexeme_generation()
