import { query } from '../db/pool.js';

export async function fetchDailyArticles({ date, category, offset, limit }) {
  const filters = ['date = $1'];
  const params = [date];

  if (category) {
    params.push(category);
    filters.push(`category = $${params.length}`);
  }

  const baseWhere = filters.length ? `where ${filters.join(' and ')}` : '';
  const listSql = `
    select id, source, title, summary, link, category, thumbnail, published_at, created_at
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

  return {
    items: listResult.rows,
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
    select id, source, title, summary, link, category, thumbnail, period_label, created_at
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

  return {
    items: listResult.rows,
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
    select distinct date
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
