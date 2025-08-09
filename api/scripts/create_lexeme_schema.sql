-- Lexeme-based database schema for Russian morphology
-- This replaces individual word cards with linguistic concepts

-- Core lexeme table
CREATE TABLE IF NOT EXISTS lexemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma TEXT NOT NULL,                    -- Base form: "дом"
    pos TEXT NOT NULL,                      -- Part of speech: "noun", "verb", "adjective"
    language TEXT NOT NULL DEFAULT 'ru',   -- Language code
    frequency_rank INT,                     -- Word frequency (1 = most common)
    cefr_level TEXT,                       -- A1, A2, B1, B2, C1, C2
    
    -- Morphological features (JSON for flexibility)
    features JSONB DEFAULT '{}'::jsonb,    -- {"gender": "m", "animacy": "inanimate"}
    
    -- Semantic information
    english_translation TEXT,              -- Primary English meaning
    semantic_field TEXT,                   -- "family", "house", "food", etc.
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Word forms table (all inflected forms of lexemes)
CREATE TABLE IF NOT EXISTS word_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lexeme_id UUID REFERENCES lexemes(id) ON DELETE CASCADE,
    form TEXT NOT NULL,                     -- Actual word form: "дома", "домом"
    grammatical_info JSONB,                 -- {"case": "genitive", "number": "singular"}
    
    -- Usage frequency of this specific form
    form_frequency REAL DEFAULT 0.0,
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- User progress tracking per lexeme (not per word form)
CREATE TABLE IF NOT EXISTS user_lexemes (
    user_id TEXT NOT NULL,
    lexeme_id UUID REFERENCES lexemes(id) ON DELETE CASCADE,
    
    -- FSRS data for this lexeme concept
    stability REAL DEFAULT 0.0,
    difficulty REAL DEFAULT 0.0,
    interval_days REAL DEFAULT 0.0,
    due_date DATE,
    reps INT DEFAULT 0,
    lapses INT DEFAULT 0,
    last_review TIMESTAMPTZ,
    state TEXT DEFAULT 'new',              -- new, learning, review, relearning
    scheduled_days INT DEFAULT 0,
    elapsed_days INT DEFAULT 0,
    
    -- Content generation tracking
    times_seen INT DEFAULT 0,              -- How many times user has seen this lexeme
    last_content_type TEXT,               -- "cloze", "vocabulary", "sentence"
    generation_history JSONB DEFAULT '[]'::jsonb,  -- Track what content was generated
    
    PRIMARY KEY (user_id, lexeme_id)
);

-- Generated content cache (avoid regenerating same content)
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lexeme_id UUID REFERENCES lexemes(id) ON DELETE CASCADE,
    content_type TEXT NOT NULL,            -- "cloze", "vocabulary", "sentence"
    cefr_level TEXT NOT NULL,             -- Target CEFR level
    
    -- The actual generated content
    payload JSONB NOT NULL,               -- Same structure as cards.payload
    
    -- Generation metadata
    prompt_hash TEXT,                     -- Hash of prompt used (detect duplicates)
    llm_model TEXT,                      -- "gpt-4", "claude-3", etc.
    generation_date TIMESTAMPTZ DEFAULT now(),
    
    -- Quality metrics
    validation_score REAL,               -- 0.0-1.0 quality score
    human_reviewed BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT TRUE,
    
    -- Usage tracking
    times_used INT DEFAULT 0,
    avg_user_rating REAL,               -- Average 1-4 rating from users
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Review log updated to track lexeme learning
CREATE TABLE IF NOT EXISTS lexeme_review_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    lexeme_id UUID REFERENCES lexemes(id) ON DELETE CASCADE,
    content_id UUID REFERENCES generated_content(id),  -- What content was shown
    
    -- Review details
    rating INT CHECK (rating BETWEEN 1 AND 4),
    response_time_ms INT,
    word_form_shown TEXT,                -- Which form was actually shown
    content_type TEXT,                   -- "cloze", "vocabulary", "sentence"
    
    -- FSRS state at time of review
    stability_before REAL,
    stability_after REAL,
    difficulty_before REAL,
    difficulty_after REAL,
    
    ts TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_lexemes_frequency ON lexemes(frequency_rank);
CREATE INDEX IF NOT EXISTS idx_lexemes_cefr ON lexemes(cefr_level);
CREATE INDEX IF NOT EXISTS idx_lexemes_pos ON lexemes(pos);
CREATE INDEX IF NOT EXISTS idx_word_forms_lexeme ON word_forms(lexeme_id);
CREATE INDEX IF NOT EXISTS idx_word_forms_form ON word_forms(form);
CREATE INDEX IF NOT EXISTS idx_user_lexemes_due ON user_lexemes(user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_generated_content_lexeme ON generated_content(lexeme_id, cefr_level);
CREATE INDEX IF NOT EXISTS idx_lexeme_review_log_user ON lexeme_review_log(user_id, ts);

-- Sample data for testing
INSERT INTO lexemes (lemma, pos, english_translation, cefr_level, frequency_rank, features, semantic_field) VALUES
('дом', 'noun', 'house', 'A1', 245, '{"gender": "masculine", "animacy": "inanimate"}', 'dwelling'),
('читать', 'verb', 'to read', 'A1', 156, '{"aspect": "imperfective", "transitivity": "transitive"}', 'activity'),
('красивый', 'adjective', 'beautiful', 'A2', 892, '{"type": "qualitative"}', 'appearance'),
('работать', 'verb', 'to work', 'A1', 203, '{"aspect": "imperfective", "transitivity": "intransitive"}', 'activity'),
('мать', 'noun', 'mother', 'A1', 334, '{"gender": "feminine", "animacy": "animate"}', 'family');

-- Sample word forms for "дом"
INSERT INTO word_forms (lexeme_id, form, grammatical_info) VALUES
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дом', '{"case": "nominative", "number": "singular"}'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дома', '{"case": "genitive", "number": "singular"}'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дому', '{"case": "dative", "number": "singular"}'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'домом', '{"case": "instrumental", "number": "singular"}'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'доме', '{"case": "prepositional", "number": "singular"}'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дома', '{"case": "nominative", "number": "plural"}'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'домов', '{"case": "genitive", "number": "plural"}');
