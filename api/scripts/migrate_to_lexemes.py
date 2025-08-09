"""
Migrate existing Russian cards to lexeme-based system
"""
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def migrate_cards_to_lexemes():
    """Convert existing cards to lexeme entries"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First, create the lexeme tables
            print("Creating lexeme schema...")
            with open('create_lexeme_schema.sql', 'r', encoding='utf-8') as f:
                cur.execute(f.read())
            
            # Get all Russian cards
            cur.execute("""
                SELECT id, type, payload 
                FROM cards 
                WHERE language = 'ru'
                ORDER BY type, id
            """)
            
            cards = cur.fetchall()
            print(f"Found {len(cards)} Russian cards to migrate")
            
            lexemes_created = 0
            
            for card in cards:
                payload = card['payload']
                if isinstance(payload, str):
                    payload = json.loads(payload)
                
                # Extract lexeme information based on card type
                if card['type'] == 'vocabulary':
                    lemma = payload.get('word', '').strip()
                    english_translation = payload.get('translation', '')
                    cefr_level = payload.get('difficulty', 'B1')
                    pos = 'noun'  # Default assumption, would need better detection
                    
                elif card['type'] == 'cloze':
                    # For cloze cards, the answer is usually the lemma
                    lemma = payload.get('answer', '').strip()
                    english_translation = payload.get('translation', '')
                    cefr_level = payload.get('difficulty', 'B1')
                    pos = 'noun'  # Would need POS detection
                    
                elif card['type'] == 'sentence':
                    # Skip sentences for now, they're more complex
                    continue
                    
                else:
                    continue
                
                if not lemma:
                    continue
                
                # Check if lexeme already exists
                cur.execute("""
                    SELECT id FROM lexemes WHERE lemma = %s AND language = 'ru'
                """, (lemma,))
                
                existing = cur.fetchone()
                
                if not existing:
                    # Create new lexeme
                    features = {}
                    
                    # Try to infer gender for nouns (basic heuristics)
                    if pos == 'noun':
                        if lemma.endswith(('а', 'я', 'ь')):
                            features['gender'] = 'feminine'
                        elif lemma.endswith(('о', 'е')):
                            features['gender'] = 'neuter'
                        else:
                            features['gender'] = 'masculine'
                        
                        # Assume inanimate unless obviously animate
                        animate_words = ['мать', 'отец', 'сын', 'дочь', 'человек', 'друг']
                        features['animacy'] = 'animate' if lemma in animate_words else 'inanimate'
                    
                    cur.execute("""
                        INSERT INTO lexemes (lemma, pos, english_translation, cefr_level, features, language)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (lemma, pos, english_translation, cefr_level, json.dumps(features), 'ru'))
                    
                    lexeme_id = cur.fetchone()['id']
                    lexemes_created += 1
                    
                    # Add the base form to word_forms
                    cur.execute("""
                        INSERT INTO word_forms (lexeme_id, form, grammatical_info)
                        VALUES (%s, %s, %s)
                    """, (lexeme_id, lemma, json.dumps({"case": "nominative", "number": "singular"})))
                    
                    print(f"Created lexeme: {lemma} ({english_translation}) - {cefr_level}")
            
            conn.commit()
            print(f"\n✅ Migration completed!")
            print(f"📊 Created {lexemes_created} lexemes")
            
            # Show summary
            cur.execute("SELECT COUNT(*) as count FROM lexemes WHERE language = 'ru'")
            total_lexemes = cur.fetchone()['count']
            
            cur.execute("SELECT cefr_level, COUNT(*) as count FROM lexemes WHERE language = 'ru' GROUP BY cefr_level ORDER BY cefr_level")
            level_breakdown = cur.fetchall()
            
            print(f"📚 Total Russian lexemes: {total_lexemes}")
            print("📈 CEFR breakdown:")
            for level in level_breakdown:
                print(f"  {level['cefr_level']}: {level['count']} lexemes")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_sample_morphology():
    """Add some sample morphological forms for common words"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    # Sample morphological data for common words
    morphology_data = {
        'дом': [
            ('дом', {"case": "nominative", "number": "singular"}),
            ('дома', {"case": "genitive", "number": "singular"}),
            ('дому', {"case": "dative", "number": "singular"}),
            ('домом', {"case": "instrumental", "number": "singular"}),
            ('доме', {"case": "prepositional", "number": "singular"}),
            ('дома', {"case": "nominative", "number": "plural"}),
            ('домов', {"case": "genitive", "number": "plural"})
        ],
        'мать': [
            ('мать', {"case": "nominative", "number": "singular"}),
            ('матери', {"case": "genitive", "number": "singular"}),
            ('матери', {"case": "dative", "number": "singular"}),
            ('матерью', {"case": "instrumental", "number": "singular"}),
            ('матери', {"case": "prepositional", "number": "singular"}),
            ('матери', {"case": "nominative", "number": "plural"})
        ]
    }
    
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            for lemma, forms in morphology_data.items():
                # Get lexeme ID
                cur.execute("SELECT id FROM lexemes WHERE lemma = %s", (lemma,))
                lexeme = cur.fetchone()
                
                if lexeme:
                    lexeme_id = lexeme['id']
                    
                    # Clear existing forms
                    cur.execute("DELETE FROM word_forms WHERE lexeme_id = %s", (lexeme_id,))
                    
                    # Add new forms
                    for form, gram_info in forms:
                        cur.execute("""
                            INSERT INTO word_forms (lexeme_id, form, grammatical_info)
                            VALUES (%s, %s, %s)
                        """, (lexeme_id, form, json.dumps(gram_info)))
                    
                    print(f"Added {len(forms)} forms for '{lemma}'")
            
            conn.commit()
            print("✅ Sample morphology added!")
            
    except Exception as e:
        print(f"❌ Error adding morphology: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Migrating to lexeme-based system...")
    migrate_cards_to_lexemes()
    print("\n📝 Adding sample morphology...")
    add_sample_morphology()
    print("\n🎉 Migration complete! Ready for LLM content generation.")
