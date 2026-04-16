CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_utc BIGINT NOT NULL,
    updated_utc BIGINT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower
    ON users (LOWER(email));

CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('VIEWER', 'ANALYST', 'REVIEWER', 'ADMIN')),
    created_utc BIGINT NOT NULL,
    updated_utc BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash TEXT NOT NULL,
    created_utc BIGINT NOT NULL,
    expires_utc BIGINT NOT NULL,
    revoked_utc BIGINT NULL,
    last_seen_utc BIGINT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_sessions_token_hash
    ON user_sessions (session_token_hash);

CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id
    ON user_sessions (user_id);

CREATE INDEX IF NOT EXISTS ix_user_sessions_expires_utc
    ON user_sessions (expires_utc);