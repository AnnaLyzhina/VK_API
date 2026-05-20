CREATE TABLE IF NOT EXISTS bot_users (
    id SERIAL PRIMARY KEY,
    vk_user_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age_from INTEGER,
    age_to INTEGER,
    sex INTEGER,
    city_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    vk_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    profile_url TEXT NOT NULL,
    city_id INTEGER,
    age INTEGER,
    sex INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS photos (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    owner_id BIGINT NOT NULL,
    photo_id BIGINT NOT NULL,
    likes_count INTEGER DEFAULT 0,
    attachment TEXT NOT NULL,
    UNIQUE(owner_id, photo_id)
);

CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    bot_user_id INTEGER NOT NULL REFERENCES bot_users(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_user_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    bot_user_id INTEGER NOT NULL REFERENCES bot_users(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_user_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS viewed_candidates (
    id SERIAL PRIMARY KEY,
    bot_user_id INTEGER NOT NULL REFERENCES bot_users(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_user_id, candidate_id)
);