"""
Test script for LLM content generation system
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

async def test_content_generation():
    """Test the content generation system without OpenAI API calls"""
    
    print("🧪 Testing Content Generation System (Mock Mode)")
    print("=" * 50)
    
    try:
        from llm.content_generator import ContentGenerator, GenerationRequest, ContentType, CEFRLevel
        import psycopg2
        
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        
        print("✅ Database connection successful")
        
        # Test database schema
        with conn.cursor() as cur:
            # Check if content generation tables exist
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name IN ('content_generation_log', 'lexemes', 'user_generation_preferences')
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            print(f"✅ Found tables: {tables}")
            
            # Check if we have any lexemes
            cur.execute("SELECT COUNT(*) FROM lexemes WHERE language = 'ru'")
            lexeme_count = cur.fetchone()[0]
            print(f"📊 Russian lexemes in database: {lexeme_count}")
            
            if lexeme_count == 0:
                print("⚠️  No Russian lexemes found. Using fallback vocabulary.")
        
        # Test content generator initialization (skip if no API key)
        if os.getenv("OPENAI_API_KEY"):
            generator = ContentGenerator(conn)
            print("✅ ContentGenerator initialized")
            
            # Test CEFR constraints
            constraints = await generator._get_cefr_vocabulary_constraints(CEFRLevel.B1)
            print(f"✅ B1 CEFR constraints: {len(constraints['allowed_words'])} words, max length: {constraints['max_sentence_length']}")
            print("\n🎯 Content Generation System Ready!")
        else:
            print("⚠️  OPENAI_API_KEY not set - skipping generator test")
            print("✅ Database schema and imports working correctly")
        print("\n📋 Next Steps:")
        print("1. Set OPENAI_API_KEY in your .env file")
        print("2. Test with: POST /v1/generate/content")
        print("3. Example request:")
        
        example_request = {
            "target_word": "читать",
            "content_type": "sentence",
            "user_cefr": "B1",
            "user_id": "test_user"
        }
        
        print(json.dumps(example_request, indent=2, ensure_ascii=False))
        
        conn.close()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the api/ directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_content_generation())
