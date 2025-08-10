# Database Schema Documentation

## Overview

The Adaptive SRS system uses PostgreSQL with Redis for caching. The schema supports spaced repetition learning, adaptive placement testing, and AI-powered content generation.

## Core Tables

### Users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    cefr_level VARCHAR(3) DEFAULT 'A1',
    language VARCHAR(10) DEFAULT 'ru',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Lexemes
```sql
CREATE TABLE lexemes (
    id SERIAL PRIMARY KEY,
    lemma VARCHAR(100) NOT NULL,
    pos VARCHAR(20) NOT NULL,
    cefr_level VARCHAR(3) NOT NULL,
    frequency_rank INTEGER,
    metadata JSONB
);
```

### Cards
```sql
CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    lexeme_id INTEGER REFERENCES lexemes(id),
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    cefr_level VARCHAR(3) NOT NULL,
    card_type VARCHAR(20) DEFAULT 'translation'
);
```

### User Cards
```sql
CREATE TABLE user_cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    card_id INTEGER REFERENCES cards(id),
    stability DECIMAL(8,4) DEFAULT 0.0,
    difficulty DECIMAL(8,4) DEFAULT 0.0,
    interval_days INTEGER DEFAULT 0,
    due_date DATE NOT NULL,
    reps INTEGER DEFAULT 0,
    lapses INTEGER DEFAULT 0,
    UNIQUE(user_id, card_id)
);
```

### Review Log
```sql
CREATE TABLE review_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    card_id INTEGER REFERENCES cards(id),
    rating INTEGER NOT NULL CHECK (rating IN (1, 2, 3, 4)),
    response_time_ms INTEGER,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Key Indexes

- `idx_users_username` on `users(username)`
- `idx_user_cards_user_due` on `user_cards(user_id, due_date)`
- `idx_cards_cefr_level` on `cards(cefr_level)`
- `idx_lexemes_lemma` on `lexemes(lemma)`

## FSRS v4 Integration

The system uses FSRS v4 algorithm parameters:
- **stability**: Memory strength (0.0 to infinity)
- **difficulty**: Card difficulty (0.0 to 1.0)
- **interval_days**: Days until next review
- **due_date**: When card is due for review

## Data Types

- **JSONB**: For flexible metadata storage
- **DECIMAL(8,4)**: For precise FSRS calculations
- **TIMESTAMP**: For audit trails and scheduling

## Performance

- Use composite indexes for common queries
- GIN indexes on JSONB fields
- Regular VACUUM and ANALYZE
- Monitor query performance with EXPLAIN
