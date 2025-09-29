// 이 파일은 PostgreSQL 연결 풀을 만들고 재사용할 수 있는 query/client 함수를 제공합니다.
// 환경 변수에 있는 접속 정보를 활용해 여러 요청을 안정적으로 처리할 수 있게 풀 크기와 타임아웃을 설정합니다.

import { Pool } from 'pg';
import { config } from '../config.js';

const pool = new Pool({
  connectionString: config.databaseUrl,
  max: 10,
  idleTimeoutMillis: 30_000,
  ssl: { rejectUnauthorized: false },
});

export const query = (text, params) => pool.query(text, params);
// `pool.query`: PostgreSQL 서버에 SQL을 날리고, 그 결과를 받아오는 함수
// text = SQL 문장
// params = 자리표시자($1, $2, $3, ...)

export const getClient = () => pool.connect();
