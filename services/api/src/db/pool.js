import { Pool } from 'pg';
import { config } from '../config.js';

const pool = new Pool({
  connectionString: config.databaseUrl,
  max: 10,
  idleTimeoutMillis: 30_000,
  ssl: { rejectUnauthorized: false },
});

export const query = (text, params) => pool.query(text, params);
export const getClient = () => pool.connect();
