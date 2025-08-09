#!/usr/bin/env python3
import os
import sys
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from repo root
THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
API_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, ".env"))

# Map CEFR -> theta for FSRS
CEFR_THETA = {"A1": -2.0, "A2": -1.0, "B1": 0.0, "B2": 1.0, "C1": 2.0, "C2": 3.0}

def db_connect_with_retry(max_retries=3):
    """Connect to database with retry logic"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD")
            )
            return conn
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise

def get_lexemes_for_generation(cur, limit=50, cefr_filter=None):
    """Get lexemes to generate cards for"""
    where_clause = "WHERE language = 'ru'"
    params = []
    
    if cefr_filter:
        where_clause += " AND cefr_level = %s"
        params.append(cefr_filter)
    
    # Prioritize high-frequency words (lower rank numbers)
    cur.execute(f"""
        SELECT id, lemma, pos, cefr_level, frequency_rank
        FROM lexemes
        {where_clause}
        ORDER BY COALESCE(frequency_rank, 999999) ASC
        LIMIT %s
    """, params + [limit])
    
    return cur.fetchall()

def create_simple_vocabulary_card(lexeme, theta):
    """Create a simple vocabulary card for a lexeme"""
    lemma = lexeme['lemma']
    pos = lexeme['pos'] or 'word'
    cefr = lexeme['cefr_level'] or 'B1'
    
    # Simple vocabulary card structure
    payload = {
        "word": lemma,
        "translation": f"[{pos}] (translate this Russian word)",
        "pos": pos,
        "target_word": lemma,
        "theta": theta,
        "cefr_level": cefr,
        "generation_method": "simple_template",
        "difficulty": cefr
    }
    
    return json.dumps(payload, ensure_ascii=False)

def create_simple_cloze_card(lexeme, theta):
    """Create a simple cloze card for a lexeme"""
    lemma = lexeme['lemma']
    pos = lexeme['pos'] or 'word'
    cefr = lexeme['cefr_level'] or 'B1'
    
    # Simple cloze card with the word blanked out
    if pos == 'v':  # verb
        text = f"Я хочу ___ это."  # "I want to ___ this"
        translation = "I want to ___ this."
    elif pos == 'noun':
        text = f"Это мой ___."  # "This is my ___"
        translation = "This is my ___."
    elif pos == 'adj':  # adjective
        text = f"Этот дом очень ___."  # "This house is very ___"
        translation = "This house is very ___."
    else:
        text = f"___ очень важно."  # "___ is very important"
        translation = "___ is very important."
    
    payload = {
        "text": text,
        "answer": lemma,
        "translation": translation,
        "target_word": lemma,
        "theta": theta,
        "cefr_level": cefr,
        "generation_method": "simple_template",
        "hints": [f"{pos}"]
    }
    
    return json.dumps(payload, ensure_ascii=False)

def generate_cards_for_lexemes(lexemes, cards_per_lexeme=2):
    """Generate cards for a list of lexemes"""
    conn = db_connect_with_retry()
    cards_created = 0
    
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for lexeme in lexemes:
                    lexeme_id = lexeme['id']
                    cefr = lexeme['cefr_level'] or 'B1'
                    theta = CEFR_THETA.get(cefr, 0.0)
                    
                    try:
                        # Create vocabulary card
                        vocab_payload = create_simple_vocabulary_card(lexeme, theta)
                        cur.execute("""
                            INSERT INTO cards (type, language, payload, lexeme_id)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, ('vocabulary', 'ru', vocab_payload, lexeme_id))
                        
                        vocab_card_id = cur.fetchone()['id']
                        cards_created += 1
                        
                        # Create cloze card if we want multiple cards per lexeme
                        if cards_per_lexeme > 1:
                            cloze_payload = create_simple_cloze_card(lexeme, theta)
                            cur.execute("""
                                INSERT INTO cards (type, language, payload, lexeme_id)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            """, ('cloze', 'ru', cloze_payload, lexeme_id))
                            
                            cloze_card_id = cur.fetchone()['id']
                            cards_created += 1
                        
                        if cards_created % 50 == 0:
                            print(f"✅ Created {cards_created} cards...")
                            conn.commit()
                            
                    except Exception as e:
                        print(f"❌ Error creating cards for lexeme '{lexeme['lemma']}': {e}")
                        continue
                
                conn.commit()
        
    except Exception as e:
        print(f"❌ Error generating cards: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return cards_created

def verify_cards():
    """Verify the generated cards"""
    conn = db_connect_with_retry()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Count cards by type
            cur.execute("""
                SELECT type, COUNT(*) as count 
                FROM cards WHERE language = 'ru' 
                GROUP BY type ORDER BY type
            """)
            card_breakdown = cur.fetchall()
            
            print("📊 Generated cards breakdown:")
            total_cards = 0
            for row in card_breakdown:
                print(f"  {row['type']}: {row['count']} cards")
                total_cards += row['count']
            print(f"  Total: {total_cards} cards")
            
            # Show sample cards
            cur.execute("""
                SELECT c.type, c.payload, l.lemma, l.cefr_level
                FROM cards c
                JOIN lexemes l ON c.lexeme_id = l.id
                WHERE c.language = 'ru'
                ORDER BY l.frequency_rank NULLS LAST
                LIMIT 5
            """)
            samples = cur.fetchall()
            
            print("\n🔤 Sample generated cards:")
            for row in samples:
                payload = row['payload']
                if isinstance(payload, str):
                    payload = json.loads(payload)
                
                target_word = payload.get('target_word', row['lemma'])
                print(f"  {row['type'].upper()}: {target_word} ({row['cefr_level']})")
                
                if row['type'] == 'vocabulary':
                    print(f"    Word: {payload.get('word', 'N/A')}")
                    print(f"    Translation: {payload.get('translation', 'N/A')}")
                elif row['type'] == 'cloze':
                    print(f"    Text: {payload.get('text', 'N/A')}")
                    print(f"    Answer: {payload.get('answer', 'N/A')}")
                print()
                
    except Exception as e:
        print(f"❌ Error verifying cards: {e}")
    finally:
        conn.close()

def main():
    print("🎯 Generating cards from lexemes...")
    
    # Get command line arguments
    limit = 100  # Start with 100 lexemes
    cefr_filter = None
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        cefr_filter = sys.argv[2].upper()
        if cefr_filter not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            cefr_filter = None
    
    print(f"📋 Parameters: limit={limit}, cefr_filter={cefr_filter or 'all'}")
    
    try:
        # Get lexemes to generate cards for
        conn = db_connect_with_retry()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            lexemes = get_lexemes_for_generation(cur, limit, cefr_filter)
        conn.close()
        
        print(f"📚 Found {len(lexemes)} lexemes to generate cards for")
        
        if not lexemes:
            print("❌ No lexemes found. Make sure lexemes are imported first.")
            return
        
        # Generate cards
        cards_created = generate_cards_for_lexemes(lexemes, cards_per_lexeme=2)
        print(f"🎉 Created {cards_created} cards from {len(lexemes)} lexemes")
        
        # Verify results
        verify_cards()
        
        print("\n✅ Card generation complete!")
        print("🚀 Ready to test the API with new lexeme-based cards")
        
    except Exception as e:
        print(f"❌ Card generation failed: {e}")

if __name__ == "__main__":
    main()
