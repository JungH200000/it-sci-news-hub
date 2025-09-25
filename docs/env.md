# Environment Variables

Reference: PRD-15-1

- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_KEY
- DATABASE_URL (optional for local tools)
- TZ=Asia/Seoul
- LOG_LEVEL (optional, default `info`)
- LOG_PRETTY (optional, default true in development)
- ALLOWED_ORIGINS (comma-separated list of allowed frontend origins)

Locations

- Root: `.env` (local only, not committed)
- Web (Next.js): `apps/web/.env.local`
- API/ingest: `services/*/.env`
