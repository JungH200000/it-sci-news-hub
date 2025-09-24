import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootEnvPath = path.resolve(__dirname, '../../.env');

dotenv.config({ path: rootEnvPath, override: false });
dotenv.config({ override: false });

const parseNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

const parseBoolean = (value, fallback) => {
  if (typeof value === 'string') {
    const lower = value.trim().toLowerCase();
    if (['true', '1', 'yes', 'y'].includes(lower)) return true;
    if (['false', '0', 'no', 'n'].includes(lower)) return false;
  }
  return fallback;
};

export const config = {
  port: parseNumber(process.env.PORT, 4000),
  databaseUrl:
    process.env.DATABASE_URL ??
    process.env.SUPABASE_DB_URL ??
    (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_KEY
      ? `${process.env.SUPABASE_URL}/postgresql`
      : null),
  requestRate: {
    windowMs: parseNumber(process.env.RATE_LIMIT_WINDOW_MS, 60_000),
    max: parseNumber(process.env.RATE_LIMIT_MAX, 120),
  },
  pagination: {
    defaultSize: parseNumber(process.env.DEFAULT_PAGE_SIZE, 10),
    maxSize: parseNumber(process.env.MAX_PAGE_SIZE, 20),
  },
  search: {
    defaultSince: process.env.SEARCH_DAYS_SINCE ?? '14 days',
    defaultLimit: parseNumber(process.env.SEARCH_DEFAULT_LIMIT, 50),
    maxLimit: parseNumber(process.env.SEARCH_MAX_LIMIT, 50),
  },
  logging: {
    level: process.env.LOG_LEVEL?.trim() || 'info',
    pretty: parseBoolean(process.env.LOG_PRETTY, process.env.NODE_ENV !== 'production'),
  },
};

if (!config.databaseUrl) {
  // eslint-disable-next-line no-console
  console.warn('DATABASE_URL is not set. Repository calls will fail without it.');
}
