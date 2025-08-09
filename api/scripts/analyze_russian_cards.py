"""
Analyze existing Russian cards and add standardized CEFR difficulty levels
"""
import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# CEFR to theta mapping for adaptive testing
CEFR_TO_THETA = {
    "A1": -2.0,
    "A2": -1.0, 
    "B1": 0.0,
    "B2": 1.0,
    "C1": 2.0,
    "C2": 3.0
}

def analyze_and_update_cards():
    """Analyze Russian cards and add theta values for placement testing"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get all Russian cards
        cur.execute("""
            SELECT id, type, payload 
            FROM cards 
            WHERE language = 'ru'
            ORDER BY type, id
        """)
        
        cards = cur.fetchall()
        print(f"Found {len(cards)} Russian cards")
        
        # Analyze difficulty distribution
        difficulty_counts = {}
        cards_by_type = {}
        
        for card in cards:
            payload = card['payload']
            if isinstance(payload, str):
                payload = json.loads(payload)
            
            card_type = card['type']
            difficulty = payload.get('difficulty', 'B1')  # Default to B1
            
            # Count difficulties
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            
            # Group by type
            if card_type not in cards_by_type:
                cards_by_type[card_type] = []
            cards_by_type[card_type].append((card['id'], payload, difficulty))
        
        print("\n📊 Current difficulty distribution:")
        for diff, count in sorted(difficulty_counts.items()):
            print(f"  {diff}: {count} cards")
        
        print(f"\n📚 Cards by type:")
        for card_type, type_cards in cards_by_type.items():
            print(f"  {card_type}: {len(type_cards)} cards")
        
        # Update cards with theta values
        updated_count = 0
        
        for card in cards:
            payload = card['payload']
            if isinstance(payload, str):
                payload = json.loads(payload)
            
            difficulty = payload.get('difficulty', 'B1')
            
            # Add theta value if not present
            if 'theta' not in payload:
                theta = CEFR_TO_THETA.get(difficulty, 0.0)
                payload['theta'] = theta
                payload['cefr'] = difficulty  # Standardize field name
                
                # Update in database
                cur.execute("""
                    UPDATE cards 
                    SET payload = %s 
                    WHERE id = %s
                """, (json.dumps(payload), card['id']))
                
                updated_count += 1
        
        print(f"\n✅ Updated {updated_count} cards with theta values")
        
        # Show sample cards from each difficulty level
        print(f"\n📋 Sample cards by difficulty:")
        for difficulty in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            cur.execute("""
                SELECT type, payload
                FROM cards 
                WHERE language = 'ru' 
                AND payload->>'difficulty' = %s
                LIMIT 2
            """, (difficulty,))
            
            samples = cur.fetchall()
            if samples:
                print(f"\n  {difficulty} ({CEFR_TO_THETA[difficulty]}θ):")
                for sample in samples:
                    payload = sample['payload']
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    
                    if sample['type'] == 'vocabulary':
                        word = payload.get('word', '')
                        translation = payload.get('translation', '')
                        print(f"    📖 {word} → {translation}")
                    elif sample['type'] == 'cloze':
                        text = payload.get('text', '')
                        answer = payload.get('answer', '')
                        print(f"    🔤 {text} (answer: {answer})")
                    elif sample['type'] == 'sentence':
                        russian = payload.get('russian', '')
                        english = payload.get('english', '')
                        print(f"    💬 {russian} → {english}")
        
        conn.commit()
        print(f"\n🎯 Russian cards are now ready for adaptive placement testing!")

if __name__ == "__main__":
    analyze_and_update_cards()
