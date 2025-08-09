import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def count_cards():
    """Count cards in the database by language and type"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    
    try:
        with conn.cursor() as cur:
            # Total count
            cur.execute("SELECT COUNT(*) FROM cards")
            total = cur.fetchone()[0]
            print(f"📊 Total cards in database: {total}")
            
            # Count by language
            cur.execute("SELECT language, COUNT(*) FROM cards GROUP BY language ORDER BY language")
            languages = cur.fetchall()
            print("\n🌍 Cards by language:")
            for lang, count in languages:
                lang_name = {"es": "Spanish", "ru": "Russian"}.get(lang, lang)
                print(f"   {lang_name} ({lang}): {count} cards")
            
            # Count by type
            cur.execute("SELECT type, COUNT(*) FROM cards GROUP BY type ORDER BY type")
            types = cur.fetchall()
            print("\n📝 Cards by type:")
            for card_type, count in types:
                print(f"   {card_type}: {count} cards")
            
            # Count by language and type
            cur.execute("SELECT language, type, COUNT(*) FROM cards GROUP BY language, type ORDER BY language, type")
            details = cur.fetchall()
            print("\n🔍 Detailed breakdown:")
            for lang, card_type, count in details:
                lang_name = {"es": "Spanish", "ru": "Russian"}.get(lang, lang)
                print(f"   {lang_name} {card_type}: {count} cards")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    count_cards()
