// 이 파일은 실제 데이터베이스와 직접 통신하는 저장소(Repository) 계층입니다.
// SQL을 실행해 일간·주간 기사 목록, 검색 결과, 사이드바 정보 등을 가져옵니다.

import { query } from '../db/pool.js';

function normalizeToYmd(d) {
  if (!d) return null; // date가 없으면 null 반환
  if (typeof d === 'string') return d.slice(0, 10);
  // 'YYYY-MM-DD' 형태면 그대로 아니면 0~9까지 slice

  // JS Date면 로컬(KST) 기준으로 YYYY-MM-DD
  // en-CA: 캐나다 영어로 `toLocaleDateString`을 하면 ISO 스타일의 날짜 포맷을 가짐 : YYYY-MM-DD
  return new Date(d).toLocaleDateString('en-CA'); // 'YYYY-MM-DD'
}

export async function fetchDailyArticles({ date, category, offset, limit }) {
  const ymd = normalizeToYmd(date); // 1) 파라미터 정규화 - date : 'YYYY-MM-DD'
  const filters = ['date = $1::date']; // 2) 명시 캐스팅
  // '$1': 자리 표시자 -> '::date'를 붙여 DB의 DATE 타입으로 강제 형 변환

  const params = [ymd];

  if (category) {
    params.push(category);
    filters.push(`category = $${params.length}`); // ['date = $1::date', 'category = $2']
  }

  const baseWhere = filters.length ? `where ${filters.join(' and ')}` : '';
  // ex) where date = 'date'::date and category = 'category';

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
  // offest ... : 최신 기사 먼저 null이면 맨 뒤로

  // 전체 게시글 수(total) 가져옴
  const countSql = `select count(*)::int as total from public.daily_articles ${baseWhere}`;

  // 목록 조회를 위한 배열
  const listParams = [...params, offset, limit];

  const [listResult, countResult] = await Promise.all([
    query(listSql, listParams), // 기사 목록 가져옴
    query(countSql, params), // 총 개수 가져옴
  ]);

  // listResult.rows : SQL이 가져온 행들(배열 형태)
  const items = listResult.rows.map((row) => ({
    ...row, // 원래 행의 모든 column 그대로 복사
    // ✅ date는 이미 'YYYY-MM-DD' 문자열. 절대 toISOString 금지
    // date: row.date,
    // published_at이 Date 객체라면 `.toISOString()`으로 변환해서 문자열로
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
    select id, week, source, title, summary, link, category, period_label, created_at, thumbnail
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
