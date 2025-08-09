-- Hybrid approach: Lexeme concepts + Individual form tracking
-- Best of both worlds for Russian morphology

-- Core lexeme table (concepts)
CREATE TABLE IF NOT EXISTS lexemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'ru',
    frequency_rank INT,
    cefr_level TEXT,
    english_translation TEXT,
    semantic_field TEXT,
    features JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- All possible word forms
CREATE TABLE IF NOT EXISTS word_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lexeme_id UUID REFERENCES lexemes(id) ON DELETE CASCADE,
    form TEXT NOT NULL,
    grammatical_info JSONB,
    form_frequency REAL DEFAULT 0.0,
    cefr_introduction_level TEXT,  -- When this form is typically learned
    created_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(lexeme_id, form)  -- Prevent duplicates
);

-- User knowledge at LEXEME level (overall concept mastery)
CREATE TABLE IF NOT EXISTS user_lexemes (
    user_id TEXT NOT NULL,
    lexeme_id UUID REFERENCES lexemes(id) ON DELETE CASCADE,
    
    -- Overall FSRS state for the concept
    stability REAL DEFAULT 0.0,
    difficulty REAL DEFAULT 0.0,
    interval_days REAL DEFAULT 0.0,
    due_date DATE,
    reps INT DEFAULT 0,
    lapses INT DEFAULT 0,
    last_review TIMESTAMPTZ,
    state TEXT DEFAULT 'new',
    scheduled_days INT DEFAULT 0,
    elapsed_days INT DEFAULT 0,
    
    -- Content generation tracking
    times_seen INT DEFAULT 0,
    generation_history JSONB DEFAULT '[]'::jsonb,
    
    PRIMARY KEY (user_id, lexeme_id)
);

-- User knowledge at WORD FORM level (morphological mastery)
CREATE TABLE IF NOT EXISTS user_word_forms (
    user_id TEXT NOT NULL,
    word_form_id UUID REFERENCES word_forms(id) ON DELETE CASCADE,
    
    -- How well user knows this specific form
    confidence_score REAL DEFAULT 0.0,  -- 0.0 = never seen, 1.0 = mastered
    times_seen INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    last_seen TIMESTAMPTZ,
    last_rating INT,  -- 1-4 from most recent review
    
    -- Morphological learning tracking
    first_encounter TIMESTAMPTZ DEFAULT now(),
    mastery_date TIMESTAMPTZ,  -- When confidence reached 0.8+
    
    PRIMARY KEY (user_id, word_form_id)
);

-- Enhanced review log tracking both levels
CREATE TABLE IF NOT EXISTS hybrid_review_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    lexeme_id UUID REFERENCES lexemes(id) ON DELETE CASCADE,
    word_form_id UUID REFERENCES word_forms(id) ON DELETE CASCADE,
    content_type TEXT,  -- "cloze", "vocabulary", "sentence"
    
    -- What was shown to user
    question_text TEXT,
    correct_answer TEXT,
    user_response TEXT,
    rating INT CHECK (rating BETWEEN 1 AND 4),
    response_time_ms INT,
    
    -- FSRS state changes at lexeme level
    lexeme_stability_before REAL,
    lexeme_stability_after REAL,
    lexeme_difficulty_before REAL,
    lexeme_difficulty_after REAL,
    
    -- Confidence changes at word form level
    form_confidence_before REAL,
    form_confidence_after REAL,
    
    ts TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_lexemes_cefr ON lexemes(cefr_level);
CREATE INDEX IF NOT EXISTS idx_word_forms_lexeme ON word_forms(lexeme_id);
CREATE INDEX IF NOT EXISTS idx_user_lexemes_due ON user_lexemes(user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_user_word_forms_confidence ON user_word_forms(user_id, confidence_score);
CREATE INDEX IF NOT EXISTS idx_hybrid_review_log_user ON hybrid_review_log(user_id, ts);

-- Sample data
INSERT INTO lexemes (lemma, pos, english_translation, cefr_level, frequency_rank, features) VALUES
('дом', 'noun', 'house', 'A1', 245, '{"gender": "masculine", "animacy": "inanimate"}'),
('читать', 'verb', 'to read', 'A1', 156, '{"aspect": "imperfective", "transitivity": "transitive"}'),
('красивый', 'adjective', 'beautiful', 'A2', 892, '{"type": "qualitative"}');

-- Word forms for "дом" with CEFR introduction levels
INSERT INTO word_forms (lexeme_id, form, grammatical_info, cefr_introduction_level) VALUES
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дом', '{"case": "nominative", "number": "singular"}', 'A1'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дома', '{"case": "genitive", "number": "singular"}', 'A2'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дому', '{"case": "dative", "number": "singular"}', 'B1'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'домом', '{"case": "instrumental", "number": "singular"}', 'B1'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'доме', '{"case": "prepositional", "number": "singular"}', 'A2'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'дома', '{"case": "nominative", "number": "plural"}', 'A2'),
((SELECT id FROM lexemes WHERE lemma = 'дом'), 'домов', '{"case": "genitive", "number": "plural"}', 'B2');
