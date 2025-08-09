import psycopg2
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

def create_lexeme_tables():
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    with conn.cursor() as cur:
        # Create lexemes table
        print("Creating lexemes table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lexemes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                language TEXT NOT NULL,
                lemma TEXT NOT NULL,
                pos TEXT,
                cefr_level TEXT,
                frequency_rank INT,
                payload JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE (language, lemma)
            )
        """)
        
        # Create user_lexemes table
        print("Creating user_lexemes table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_lexemes (
                user_id TEXT NOT NULL,
                lexeme_id UUID NOT NULL REFERENCES lexemes(id),
                stability REAL DEFAULT 0,
                difficulty REAL DEFAULT 0.3,
                interval_days REAL DEFAULT 0,
                due_date DATE,
                reps INT DEFAULT 0,
                lapses INT DEFAULT 0,
                last_review TIMESTAMPTZ,
                state TEXT DEFAULT 'new',
                scheduled_days INTEGER DEFAULT 0,
                elapsed_days INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, lexeme_id)
            )
        """)
        
        # Create content generation log table
        print("Creating content_generation_log table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS content_generation_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id TEXT NOT NULL,
                card_id TEXT,
                target_word TEXT NOT NULL,
                content_type TEXT NOT NULL,
                cefr_level TEXT NOT NULL,
                generation_method TEXT NOT NULL,
                prompt_used TEXT,
                llm_response TEXT,
                generation_time_ms INTEGER,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Add indexes
        print("Adding indexes...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lexemes_language_lemma ON lexemes (language, lemma)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_lexemes_user_id ON user_lexemes (user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_content_generation_log_user_id ON content_generation_log (user_id)")
        
        # Insert some sample Russian lexemes for testing
        print("Inserting sample Russian lexemes...")
        sample_lexemes = [
            ('читать', 'verb', 'B1', 150),
            ('изучать', 'verb', 'B2', 300),
            ('понимать', 'verb', 'A2', 100),
            ('говорить', 'verb', 'A2', 80),
            ('есть', 'verb', 'A1', 20),
            ('дом', 'noun', 'A1', 50),
            ('работать', 'verb', 'A2', 120),
            ('думать', 'verb', 'B1', 180),
            ('знать', 'verb', 'A2', 90),
            ('видеть', 'verb', 'A2', 110)
        ]
        
        for lemma, pos, cefr, freq in sample_lexemes:
            cur.execute("""
                INSERT INTO lexemes (language, lemma, pos, cefr_level, frequency_rank)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (language, lemma) DO NOTHING
            """, ('ru', lemma, pos, cefr, freq))
        
        conn.commit()
        print("✅ Lexeme tables created successfully!")
        
        # Check results
        cur.execute("SELECT COUNT(*) FROM lexemes WHERE language = 'ru'")
        count = cur.fetchone()[0]
        print(f"📊 Russian lexemes in database: {count}")
    
    conn.close()

if __name__ == "__main__":
    create_lexeme_tables()
