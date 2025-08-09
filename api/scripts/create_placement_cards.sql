-- CEFR Placement Test Cards
-- Each card has a known difficulty level (theta) for adaptive testing

-- A1 Level Cards (θ = -2.0) - Very Basic
INSERT INTO cards(language, type, payload) VALUES
('en', 'placement', '{"text": "I ___ hungry.", "answer": "am", "options": ["am", "is", "are", "be"], "cefr": "A1", "theta": -2.0, "topic": "basic_verbs"}'),
('en', 'placement', '{"text": "This is my ___.", "answer": "book", "options": ["book", "books", "booking", "booked"], "cefr": "A1", "theta": -2.0, "topic": "possessives"}'),
('en', 'placement', '{"text": "She ___ from Spain.", "answer": "is", "options": ["am", "is", "are", "be"], "cefr": "A1", "theta": -1.8, "topic": "countries"}'),

-- A2 Level Cards (θ = -1.0) - Elementary
('en', 'placement', '{"text": "I ___ to the store yesterday.", "answer": "went", "options": ["go", "went", "going", "goes"], "cefr": "A2", "theta": -1.0, "topic": "past_simple"}'),
('en', 'placement', '{"text": "There ___ many people at the party.", "answer": "were", "options": ["was", "were", "are", "is"], "cefr": "A2", "theta": -1.2, "topic": "past_plural"}'),
('en', 'placement', '{"text": "I ___ pizza for dinner tonight.", "answer": "will have", "options": ["have", "had", "will have", "having"], "cefr": "A2", "theta": -0.8, "topic": "future_simple"}'),

-- B1 Level Cards (θ = 0.0) - Intermediate  
('en', 'placement', '{"text": "If I ___ you, I would study harder.", "answer": "were", "options": ["am", "was", "were", "be"], "cefr": "B1", "theta": 0.0, "topic": "conditionals"}'),
('en', 'placement', '{"text": "She has been ___ English for five years.", "answer": "studying", "options": ["study", "studied", "studying", "studies"], "cefr": "B1", "theta": 0.2, "topic": "present_perfect_continuous"}'),
('en', 'placement', '{"text": "The movie ___ by millions of people.", "answer": "was watched", "options": ["watched", "was watched", "is watching", "watches"], "cefr": "B1", "theta": -0.2, "topic": "passive_voice"}'),

-- B2 Level Cards (θ = 1.0) - Upper-Intermediate
('en', 'placement', '{"text": "I wish I ___ more time to travel.", "answer": "had", "options": ["have", "had", "will have", "would have"], "cefr": "B2", "theta": 1.0, "topic": "subjunctive"}'),
('en', 'placement', '{"text": "The project ___ completed by next month.", "answer": "will have been", "options": ["will be", "will have been", "would be", "would have been"], "cefr": "B2", "theta": 1.2, "topic": "future_perfect_passive"}'),
('en', 'placement', '{"text": "She spoke ___ confidently that everyone believed her.", "answer": "so", "options": ["so", "such", "very", "too"], "cefr": "B2", "theta": 0.8, "topic": "intensifiers"}'),

-- C1 Level Cards (θ = 2.0) - Advanced
('en', 'placement', '{"text": "The proposal was ___ rejected due to budget constraints.", "answer": "summarily", "options": ["summarily", "summary", "summarize", "summarized"], "cefr": "C1", "theta": 2.0, "topic": "formal_vocabulary"}'),
('en', 'placement', '{"text": "Had she not intervened, the situation ___ much worse.", "answer": "could have been", "options": ["would be", "could have been", "might be", "should be"], "cefr": "C1", "theta": 2.2, "topic": "complex_conditionals"}'),
('en', 'placement', '{"text": "The ___ of the argument was difficult to follow.", "answer": "intricacies", "options": ["intricacies", "complications", "difficulties", "problems"], "cefr": "C1", "theta": 1.8, "topic": "abstract_concepts"}'),

-- C2 Level Cards (θ = 3.0) - Proficiency
('en', 'placement', '{"text": "His ___ remarks left the audience speechless.", "answer": "perspicacious", "options": ["perspicacious", "perspiration", "perspective", "persistent"], "cefr": "C2", "theta": 3.0, "topic": "advanced_vocabulary"}'),
('en', 'placement', '{"text": "The research ___ new insights into human behavior.", "answer": "yielded", "options": ["yielded", "produced", "created", "made"], "cefr": "C2", "theta": 2.8, "topic": "academic_register"}'),
('en', 'placement', '{"text": "She is ___ regarded as an expert in her field.", "answer": "universally", "options": ["universally", "generally", "commonly", "usually"], "cefr": "C2", "theta": 3.2, "topic": "precision_adverbs"}');

-- Create placement test sessions table
CREATE TABLE IF NOT EXISTS placement_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    current_theta REAL DEFAULT 0.0,
    theta_se REAL DEFAULT 1.0, -- Standard error
    items_completed INT DEFAULT 0,
    is_complete BOOLEAN DEFAULT FALSE,
    final_cefr TEXT,
    final_theta REAL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Track individual placement responses
CREATE TABLE IF NOT EXISTS placement_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES placement_sessions(id),
    card_id UUID REFERENCES cards(id),
    user_response TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    response_time_ms INT,
    theta_before REAL,
    theta_after REAL,
    se_before REAL,
    se_after REAL,
    created_at TIMESTAMPTZ DEFAULT now()
);
