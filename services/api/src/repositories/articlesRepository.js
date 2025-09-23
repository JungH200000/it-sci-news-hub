import { query } from '../db/pool.js';

function normalizeToYmd(d) {
  if (!d) return null;
  if (typeof d === 'string') return d.slice(0, 10); // 'YYYY-MM-DD' 형태면 그대로
  // JS Date면 로컬(KST) 기준으로 YYYY-MM-DD 뽑기
  return new Date(d).toLocaleDateString('en-CA'); // 'YYYY-MM-DD'
}

export async function fetchDailyArticles({ date, category, offset, limit }) {
  const ymd = normalizeToYmd(date); // ✅ 1) 파라미터 정규화
  const filters = ['date = $1::date']; // ✅ 2) 명시 캐스팅
  const params = [ymd];

  if (category) {
    params.push(category);
    filters.push(`category = $${params.length}`);
  }

  const baseWhere = filters.length ? `where ${filters.join(' and ')}` : '';
  const listSql = `
    select
      id,
      source,
      title,
      summary,
      link,
      category,
      thumbnail,
      published_at,
      created_at,
      date::text as date
    from public.daily_articles
    ${baseWhere}
    order by published_at desc nulls last, created_at desc
    offset $${params.length + 1} limit $${params.length + 2}
  `;
  const countSql = `select count(*)::int as total from public.daily_articles ${baseWhere}`;

  const listParams = [...params, offset, limit];

  const [listResult, countResult] = await Promise.all([
    query(listSql, listParams),
    query(countSql, params),
  ]);

  const items = listResult.rows.map((row) => ({
    ...row,
    // ✅ date는 이미 'YYYY-MM-DD' 문자열. 절대 toISOString 금지
    // date: row.date,
    // published_at은 필요하면 그대로 두거나, 문자열로 다루세요.
    published_at:
      row.published_at instanceof Date ? row.published_at.toISOString() : row.published_at,
  }));

  return {
    items,
    total: countResult.rows[0]?.total ?? 0,
  };
}

export async function fetchWeeklyArticles({ week, category, offset, limit }) {
  const filters = ['week = $1'];
  const params = [week];

  if (category) {
    params.push(category);
    filters.push(`category = $${params.length}`);
  }

  const baseWhere = filters.length ? `where ${filters.join(' and ')}` : '';
  const listSql = `
    select id, source, title, summary, link, category, period_label, created_at
    from public.weekly_articles
    ${baseWhere}
    order by created_at desc
    offset $${params.length + 1} limit $${params.length + 2}
  `;
  const countSql = `select count(*)::int as total from public.weekly_articles ${baseWhere}`;

  const listParams = [...params, offset, limit];

  const [listResult, countResult] = await Promise.all([
    query(listSql, listParams),
    query(countSql, params),
  ]);

  const items = listResult.rows.map((row) => ({
    ...row,
    week: row.week,
    date: row.date instanceof Date ? row.date.toISOString().slice(0, 10) : row.date,
  }));

  return {
    items,
    total: countResult.rows[0]?.total ?? 0,
  };
}

export async function searchUnified({ q, cat, dSince, limit }) {
  const sql = 'select * from public.search_unified($1, $2, $3, $4)';
  const result = await query(sql, [q, cat, dSince, limit]);
  return result.rows;
}

export async function fetchDailyDates(limit = 14) {
  const sql = `
    select distinct date::text as date
    from public.daily_articles
    order by date desc
    limit $1
  `;
  const result = await query(sql, [limit]);
  return result.rows.map((row) => row.date);
}

export async function fetchWeeklyWeeks(limit = 8) {
  const sql = `
    select distinct week
    from public.weekly_articles
    order by week desc
    limit $1
  `;
  const result = await query(sql, [limit]);
  return result.rows.map((row) => row.week);
}
