// 이 파일은 컨트롤러와 데이터베이스 사이의 비즈니스 로직을 담당합니다.
// 요청 파라미터를 검사하고 페이지네이션을 계산한 다음, 리포지토리에서 가져온 데이터를 화면에서 쓰기 좋은 구조로 가공합니다.

import { config } from '../config.js';
import {
  fetchDailyArticles,
  fetchWeeklyArticles,
  searchUnified,
  fetchDailyDates,
  fetchWeeklyWeeks,
} from '../repositories/articlesRepository.js';
import { badRequest } from '../utils/httpErrors.js';
import { parsePagination } from '../utils/pagination.js';

const DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;
const WEEK_REGEX = /^\d{4}-\d{2}-[1-5]$/;

export async function getDailyArticles(params) {
  const { date, category: rawCategory, page, size } = params;
  const category = rawCategory?.trim() || null;

  if (!Date.parse(date) || !DATE_REGEX.test(date)) {
    throw badRequest('Query parameter "date" must be YYYY-MM-DD.');
  }

  const pagination = parsePagination({ page, size }, config.pagination);

  const { items, total } = await fetchDailyArticles({
    date,
    category,
    offset: pagination.offset,
    limit: pagination.size,
  });

  return {
    items,
    page: pagination.page,
    size: pagination.size,
    total,
    hasMore: pagination.offset + items.length < total,
    filters: {
      date,
      category,
    },
  };
}

export async function getWeeklyArticles(params) {
  const { week, category: rawCategory, page, size } = params;
  const category = rawCategory?.trim() || null;

  if (!WEEK_REGEX.test(week)) {
    throw badRequest('Query parameter "week" must be YYYY-MM-N (N=1~5).');
  }

  const pagination = parsePagination({ page, size }, config.pagination);

  const { items, total } = await fetchWeeklyArticles({
    week,
    category,
    offset: pagination.offset,
    limit: pagination.size,
  });

  return {
    items,
    page: pagination.page,
    size: pagination.size,
    total,
    hasMore: pagination.offset + items.length < total,
    filters: {
      week,
      category,
    },
  };
}

export async function getSearchResults(params) {
  const { q, cat, limit } = params;
  const trimmed = q?.trim();
  if (!trimmed) {
    throw badRequest('Query parameter "q" is required.');
  }

  const maxLimit = config.search.maxLimit;
  const requestedLimit = Number.parseInt(limit, 10);
  const effectiveLimit = Number.isFinite(requestedLimit) && requestedLimit > 0
    ? Math.min(requestedLimit, maxLimit)
    : config.search.defaultLimit;

  const rows = await searchUnified({
    q: trimmed,
    cat: cat?.trim() ? cat.trim() : null,
    dSince: config.search.defaultSince,
    limit: effectiveLimit,
  });

  const daily = [];
  const weekly = [];

  rows.forEach((row) => {
    const base = {
      id: row.id,
      source: row.source,
      title: row.title,
      summary: row.summary,
      link: row.link,
      category: row.category,
      sort_time: row.sort_time,
      rank: row.rank,
      thumbnail: row.thumbnail,
    };
    if (row.kind === 'daily') {
      daily.push({ ...base, date: row.date_key, published_at: row.published_at });
    } else {
      weekly.push({
        ...base,
        week: row.week_key,
        period_label: row.period_label,
      });
    }
  });

  return {
    query: trimmed,
    filters: {
      category: cat?.trim() || null,
      limit: effectiveLimit,
    },
    results: {
      daily,
      weekly,
    },
  };
}

export async function getDailySidebar(limit = 14) {
  return fetchDailyDates(limit);
}

export async function getWeeklySidebar(limit = 8) {
  return fetchWeeklyWeeks(limit);
}
