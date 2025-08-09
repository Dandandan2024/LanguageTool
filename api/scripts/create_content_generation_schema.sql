-- Content Generation Schema
-- Tables to track LLM-generated content and generation history

-- Table to log all content generation requests and results
CREATE TABLE IF NOT EXISTS content_generation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    card_id TEXT, -- References cards.id (may be NULL if generation failed)
    target_word TEXT NOT NULL,
    content_type TEXT NOT NULL, -- 'vocabulary', 'sentence', 'cloze'
    cefr_level TEXT NOT NULL,
    generation_method TEXT NOT NULL, -- 'llm_vocabulary', 'llm_sentence', 'llm_cloze'
    prompt_used TEXT, -- The actual prompt sent to LLM (for debugging)
    llm_response TEXT, -- Raw LLM response (for analysis)
    generation_time_ms INTEGER, -- Time taken to generate
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT, -- If generation failed
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table to track content generation jobs (for async/batch processing)
CREATE TABLE IF NOT EXISTS content_generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    job_type TEXT NOT NULL, -- 'single', 'batch', 'scheduled'
    status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    request_payload JSONB NOT NULL, -- Original request parameters
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 1,
    card_ids TEXT[], -- Array of generated card IDs
    error_details TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table to track user preferences for content generation
CREATE TABLE IF NOT EXISTS user_generation_preferences (
    user_id TEXT PRIMARY KEY,
    preferred_content_types TEXT[] DEFAULT ARRAY['sentence', 'vocabulary'], -- Preferred types
    difficulty_adjustment REAL DEFAULT 0.0, -- User-specific difficulty adjustment (-1.0 to 1.0)
    avoid_topics TEXT[] DEFAULT ARRAY[]::TEXT[], -- Topics/themes to avoid
    preferred_topics TEXT[] DEFAULT ARRAY[]::TEXT[], -- Preferred topics/themes
    max_sentence_length INTEGER, -- Override default sentence length
    generation_frequency TEXT DEFAULT 'normal', -- 'low', 'normal', 'high'
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Table to store content quality ratings from users
CREATE TABLE IF NOT EXISTS content_quality_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    card_id TEXT NOT NULL, -- References cards.id
    quality_rating INTEGER NOT NULL CHECK (quality_rating BETWEEN 1 AND 5), -- 1=poor, 5=excellent
    difficulty_rating INTEGER CHECK (difficulty_rating BETWEEN 1 AND 5), -- 1=too easy, 5=too hard
    relevance_rating INTEGER CHECK (relevance_rating BETWEEN 1 AND 5), -- 1=not relevant, 5=very relevant
    feedback_text TEXT, -- Optional text feedback
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, card_id) -- One rating per user per card
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_content_generation_log_user_id ON content_generation_log (user_id);
CREATE INDEX IF NOT EXISTS idx_content_generation_log_created_at ON content_generation_log (created_at);
CREATE INDEX IF NOT EXISTS idx_content_generation_log_target_word ON content_generation_log (target_word);
CREATE INDEX IF NOT EXISTS idx_content_generation_log_success ON content_generation_log (success);

CREATE INDEX IF NOT EXISTS idx_content_generation_jobs_user_id ON content_generation_jobs (user_id);
CREATE INDEX IF NOT EXISTS idx_content_generation_jobs_status ON content_generation_jobs (status);
CREATE INDEX IF NOT EXISTS idx_content_generation_jobs_created_at ON content_generation_jobs (created_at);

CREATE INDEX IF NOT EXISTS idx_content_quality_ratings_user_id ON content_quality_ratings (user_id);
CREATE INDEX IF NOT EXISTS idx_content_quality_ratings_card_id ON content_quality_ratings (card_id);
CREATE INDEX IF NOT EXISTS idx_content_quality_ratings_quality_rating ON content_quality_ratings (quality_rating);

-- Add some sample user preferences for testing
INSERT INTO user_generation_preferences (user_id, preferred_content_types, difficulty_adjustment)
VALUES 
    ('anonymous', ARRAY['sentence', 'vocabulary'], 0.0),
    ('Jacob', ARRAY['sentence', 'cloze'], 0.2)
ON CONFLICT (user_id) DO NOTHING;
