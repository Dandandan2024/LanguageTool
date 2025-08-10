"""
Quick test of LLM content generation with your OpenAI API key
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

async def test_live_generation():
    """Test actual content generation with OpenAI API"""
    
    print("🚀 Testing LIVE Content Generation with OpenAI")
    print("=" * 50)
    
    try:
        from llm.content_generator import ContentGenerator, GenerationRequest, ContentType, CEFRLevel
        import psycopg2
        
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ No OpenAI API key found in .env file")
            return
        
        print(f"✅ OpenAI API key found: {api_key[:20]}...")
        
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        
        print("✅ Database connected")
        
        # Create generator
        generator = ContentGenerator(conn)
        print("✅ ContentGenerator initialized")
        
        # Test 1: Generate a vocabulary card
        print("\n🧪 Test 1: Generating Vocabulary Card for 'читать' (B1 level)")
        vocab_request = GenerationRequest(
            target_word="читать",
            target_lexeme_id="temp_читать",
            content_type=ContentType.VOCABULARY,
            user_cefr=CEFRLevel.B1,
            user_id="test_user"
        )
        
        vocab_content = await generator.generate_content(vocab_request)
        
        print("📋 Generated Vocabulary Card:")
        print(f"  Question: {vocab_content.question_text}")
        print(f"  Answer: {vocab_content.answer_text}")
        print(f"  Target: {vocab_content.target_word}")
        print(f"  Supporting words: {vocab_content.supporting_words}")
        
        # Test 2: Generate a sentence card
        print("\n🧪 Test 2: Generating Sentence Card for 'изучать' (B2 level)")
        sentence_request = GenerationRequest(
            target_word="изучать",
            target_lexeme_id="temp_изучать",
            content_type=ContentType.SENTENCE,
            user_cefr=CEFRLevel.B2,
            user_id="test_user"
        )
        
        sentence_content = await generator.generate_content(sentence_request)
        
        print("📋 Generated Sentence Card:")
        print(f"  Question: {sentence_content.question_text}")
        print(f"  Answer: {sentence_content.answer_text}")
        print(f"  Target: {sentence_content.target_word}")
        print(f"  Supporting words: {sentence_content.supporting_words}")
        
        # Test 3: Generate a cloze card
        print("\n🧪 Test 3: Generating Cloze Card for 'понимать' (A2 level)")
        cloze_request = GenerationRequest(
            target_word="понимать",
            target_lexeme_id="temp_понимать",
            content_type=ContentType.CLOZE,
            user_cefr=CEFRLevel.A2,
            user_id="test_user"
        )
        
        cloze_content = await generator.generate_content(cloze_request)
        
        print("📋 Generated Cloze Card:")
        print(f"  Question: {cloze_content.question_text}")
        print(f"  Answer: {cloze_content.answer_text}")
        print(f"  Target: {cloze_content.target_word}")
        print(f"  Supporting words: {cloze_content.supporting_words}")
        
        print("\n🎉 SUCCESS! LLM Content Generation is working perfectly!")
        print("\n📊 Next Steps:")
        print("1. Deploy your updated backend to Railway")
        print("2. Test the API endpoints from your frontend")
        print("3. Generate content for any Russian word you want to learn!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_generation())

