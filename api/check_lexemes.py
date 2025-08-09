#!/usr/bin/env python3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join('..', '.env'))

def check_database_state():
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check if lexemes table exists and has data
        cur.execute("SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = 'lexemes'")
        table_exists = cur.fetchone()['count'] > 0
        print(f'Lexemes table exists: {table_exists}')
        
        if table_exists:
            cur.execute("SELECT COUNT(*) as count FROM lexemes WHERE language = 'ru'")
            lexeme_count = cur.fetchone()['count']
            print(f'Russian lexemes in database: {lexeme_count}')
            
            if lexeme_count > 0:
                cur.execute("SELECT cefr_level, COUNT(*) as count FROM lexemes WHERE language = 'ru' GROUP BY cefr_level ORDER BY cefr_level")
                breakdown = cur.fetchall()
                print('CEFR breakdown:')
                for row in breakdown:
                    print(f'  {row["cefr_level"]}: {row["count"]} lexemes')
                    
                # Show sample lexemes
                cur.execute("SELECT lemma, pos, cefr_level, frequency_rank FROM lexemes WHERE language = 'ru' ORDER BY frequency_rank LIMIT 10")
                samples = cur.fetchall()
                print('\nSample lexemes (by frequency):')
                for row in samples:
                    print(f'  {row["lemma"]} ({row["pos"]}) - {row["cefr_level"]} - rank {row["frequency_rank"]}')
        
        # Check cards table
        cur.execute("SELECT COUNT(*) as count FROM cards WHERE language = 'ru'")
        card_count = cur.fetchone()['count']
        print(f'\nRussian cards in database: {card_count}')
        
        # Check if cards have lexeme_id column
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'cards' AND column_name = 'lexeme_id'
        """)
        has_lexeme_id = cur.fetchone()['count'] > 0
        print(f'Cards table has lexeme_id column: {has_lexeme_id}')

    conn.close()

if __name__ == "__main__":
    check_database_state()
