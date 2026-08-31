-- Records which deployment environment owns this database.
--
-- Production and staging must never share a database. Configuration alone
-- cannot guarantee that: one wrong DATABASE_URL on a Render service silently
-- points staging at production data, and nothing fails until real damage is
-- done. Stamping the database itself makes the mismatch detectable, so the
-- guard in app/persistence/environment.py can refuse to run.
--
-- Single-row table: the CHECK constraint pins the primary key so a second row
-- cannot be inserted.
CREATE TABLE IF NOT EXISTS deployment_environment (
    id BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (id),
    environment TEXT NOT NULL,
    stamped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
