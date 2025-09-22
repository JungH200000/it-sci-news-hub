# DB Migration Policy

Reference: PRD-6, PRD-16

Order (idempotent, incremental)

1. 001_tables – daily/weekly tables
2. 002_indexes – listing/sort/unique/trgm indexes
3. 003_tsv_triggers – add `tsv` columns and triggers
4. 004_views – `unified_articles` view
5. 005_search_rpc – `search_unified` RPC (section caps)
(optional) 006_policies – RLS (read-only)
(optional) 007_retention_jobs – retention SQL

Notes

- Each step must not depend on later steps.
- Apply safely multiple times (IF NOT EXISTS, CREATE OR REPLACE).

