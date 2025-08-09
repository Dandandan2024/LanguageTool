import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

def add_russian_content():
    """Add Russian language learning content to the database"""
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adaptive_srs"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    conn.autocommit = True
    
    # Sample Russian content - replace with ChatGPT generated content
    russian_cards = [
        # Vocabulary cards
        ("ru", "vocabulary", '{"word": "привет", "translation": "hello", "difficulty": "A1"}'),
        ("ru", "vocabulary", '{"word": "спасибо", "translation": "thank you", "difficulty": "A1"}'),
        ("ru", "vocabulary", '{"word": "пожалуйста", "translation": "please/you\'re welcome", "difficulty": "A1"}'),
        ("ru", "vocabulary", '{"word": "да", "translation": "yes", "difficulty": "A1"}'),
        ("ru", "vocabulary", '{"word": "нет", "translation": "no", "difficulty": "A1"}'),
        
        # Cloze cards
        ("ru", "cloze", '{"text": "Меня зовут ___.", "answer": "Анна", "hints": ["female name"], "translation": "My name is ___."}'),
        ("ru", "cloze", '{"text": "Я говорю по-___.", "answer": "русски", "hints": ["language"], "translation": "I speak ___."}'),
        ("ru", "cloze", '{"text": "Сколько это ___?", "answer": "стоит", "hints": ["verb meaning costs"], "translation": "How much does this ___?"}'),
        
        # Sentence cards
        ("ru", "sentence", '{"russian": "Как дела?", "english": "How are things?", "difficulty": "A1"}'),
        ("ru", "sentence", '{"russian": "Меня зовут Иван.", "english": "My name is Ivan.", "difficulty": "A1"}'),
        ("ru", "sentence", '{"russian": "Я изучаю русский язык.", "english": "I am studying Russian.", "difficulty": "A2"}'),
    ]
    
    with conn.cursor() as cur:
        for language, card_type, payload in russian_cards:
            cur.execute(
                "INSERT INTO cards(language, type, payload) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                (language, card_type, payload)
            )
        
        print(f"Added {len(russian_cards)} Russian cards to the database!")
    
    conn.close()

if __name__ == "__main__":
    add_russian_content()
