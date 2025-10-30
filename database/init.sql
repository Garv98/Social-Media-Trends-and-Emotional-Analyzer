-- Initialize Twitter Sentiment Database Schema

-- Create database if not exists (for development)
-- In production, this should be done separately

-- Create tweets table
CREATE TABLE IF NOT EXISTS tweets (
    id BIGINT PRIMARY KEY,
    original_text TEXT NOT NULL,
    cleaned_text TEXT,
    ml_text TEXT,
    created_at TIMESTAMP NOT NULL,
    author_id BIGINT,
    author_username VARCHAR(255),
    retweet_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,
    char_count INTEGER,
    word_count INTEGER,
    hashtag_count INTEGER DEFAULT 0,
    mention_count INTEGER DEFAULT 0,
    url_count INTEGER DEFAULT 0,
    token_count INTEGER,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Create hashtags table
CREATE TABLE IF NOT EXISTS hashtags (
    id SERIAL PRIMARY KEY,
    hashtag VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tweet_hashtags junction table (many-to-many)
CREATE TABLE IF NOT EXISTS tweet_hashtags (
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    hashtag_id INTEGER REFERENCES hashtags(id) ON DELETE CASCADE,
    PRIMARY KEY (tweet_id, hashtag_id)
);

-- Create mentions table
CREATE TABLE IF NOT EXISTS mentions (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create urls table
CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sentiment_predictions table (for ML model results)
CREATE TABLE IF NOT EXISTS sentiment_predictions (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    sentiment VARCHAR(50) NOT NULL, -- positive, negative, neutral
    confidence FLOAT NOT NULL,
    model_version VARCHAR(100),
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tweet_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
CREATE INDEX IF NOT EXISTS idx_tweets_processed ON tweets(processed);
CREATE INDEX IF NOT EXISTS idx_tweets_author_id ON tweets(author_id);
CREATE INDEX IF NOT EXISTS idx_tweet_hashtags_hashtag_id ON tweet_hashtags(hashtag_id);
CREATE INDEX IF NOT EXISTS idx_tweet_hashtags_tweet_id ON tweet_hashtags(tweet_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_predictions_tweet_id ON sentiment_predictions(tweet_id);
CREATE INDEX IF NOT EXISTS idx_hashtags_hashtag ON hashtags(hashtag);
CREATE INDEX IF NOT EXISTS idx_mentions_tweet_id ON mentions(tweet_id);
CREATE INDEX IF NOT EXISTS idx_urls_tweet_id ON urls(tweet_id);

-- Create view for analytics
CREATE OR REPLACE VIEW tweet_analytics AS
SELECT 
    t.id,
    t.original_text,
    t.cleaned_text,
    t.created_at,
    t.author_username,
    t.retweet_count,
    t.like_count,
    t.reply_count,
    t.quote_count,
    t.char_count,
    t.word_count,
    t.hashtag_count,
    t.mention_count,
    STRING_AGG(DISTINCT h.hashtag, ', ') as hashtags,
    sp.sentiment,
    sp.confidence as sentiment_confidence,
    sp.model_version
FROM tweets t
LEFT JOIN tweet_hashtags th ON t.id = th.tweet_id
LEFT JOIN hashtags h ON th.hashtag_id = h.id
LEFT JOIN sentiment_predictions sp ON t.id = sp.tweet_id
GROUP BY t.id, t.original_text, t.cleaned_text, t.created_at, t.author_username,
         t.retweet_count, t.like_count, t.reply_count, t.quote_count,
         t.char_count, t.word_count, t.hashtag_count, t.mention_count,
         sp.sentiment, sp.confidence, sp.model_version;

-- Create view for hashtag statistics
CREATE OR REPLACE VIEW hashtag_stats AS
SELECT 
    h.hashtag,
    COUNT(DISTINCT t.id) as tweet_count,
    AVG(t.retweet_count) as avg_retweets,
    AVG(t.like_count) as avg_likes,
    AVG(t.char_count) as avg_char_count,
    COUNT(DISTINCT t.author_id) as unique_authors,
    MAX(t.created_at) as latest_tweet,
    MIN(t.created_at) as earliest_tweet,
    COUNT(CASE WHEN sp.sentiment = 'positive' THEN 1 END) as positive_count,
    COUNT(CASE WHEN sp.sentiment = 'negative' THEN 1 END) as negative_count,
    COUNT(CASE WHEN sp.sentiment = 'neutral' THEN 1 END) as neutral_count
FROM hashtags h
LEFT JOIN tweet_hashtags th ON h.id = th.hashtag_id
LEFT JOIN tweets t ON th.tweet_id = t.id
LEFT JOIN sentiment_predictions sp ON t.id = sp.tweet_id
GROUP BY h.hashtag;

-- Insert some default hashtags for tracking
INSERT INTO hashtags (hashtag) VALUES 
    ('ai'),
    ('machinelearning'),
    ('datascience'),
    ('nlp'),
    ('deeplearning'),
    ('python'),
    ('tensorflow'),
    ('pytorch')
ON CONFLICT (hashtag) DO NOTHING;

-- Create a function to update tweet counts
CREATE OR REPLACE FUNCTION update_tweet_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update hashtag count
    NEW.hashtag_count = (
        SELECT COUNT(*)
        FROM regexp_split_to_table(NEW.original_text, '\s+') as word
        WHERE word ~ '^#\w+'
    );
    
    -- Update mention count
    NEW.mention_count = (
        SELECT COUNT(*)
        FROM regexp_split_to_table(NEW.original_text, '\s+') as word
        WHERE word ~ '^@\w+'
    );
    
    -- Update URL count
    NEW.url_count = (
        SELECT COUNT(*)
        FROM regexp_split_to_table(NEW.original_text, '\s+') as word
        WHERE word ~ '^https?://'
    );
    
    -- Update word count
    NEW.word_count = (
        SELECT COUNT(*)
        FROM regexp_split_to_table(NEW.original_text, '\s+') as word
        WHERE word != ''
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update counts
CREATE TRIGGER update_tweet_counts_trigger
    BEFORE INSERT OR UPDATE ON tweets
    FOR EACH ROW
    EXECUTE FUNCTION update_tweet_counts();

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
