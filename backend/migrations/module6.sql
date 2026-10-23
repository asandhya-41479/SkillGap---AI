-- Module 6 migration. Safe to run more than once.
-- New tables (progress_evidence, readiness_snapshots) are created by Base.metadata.create_all on
-- server start. create_all never ALTERs existing tables, so the three new columns go here.
BEGIN;

ALTER TABLE roadmap_items     ADD COLUMN IF NOT EXISTS notes            VARCHAR(500);
ALTER TABLE roadmap_items     ADD COLUMN IF NOT EXISTS practical_done   BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE skill_gap_results ADD COLUMN IF NOT EXISTS evidence_adjusted BOOLEAN NOT NULL DEFAULT false;

COMMIT;