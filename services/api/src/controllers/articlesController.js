// 이 파일은 요청별로 서비스 함수를 호출해 JSON 형태의 응답을 돌려주는 컨트롤러 묶음입니다.
// try/catch로 에러를 잡아 next에 넘기면, 공통 에러 핸들러가 알아서 처리합니다.

import {
  getDailyArticles,
  getWeeklyArticles,
  getSearchResults,
  getDailySidebar,
  getWeeklySidebar,
} from '../services/articlesService.js';

export async function handleDailyArticles(req, res, next) {
  try {
    // req.query : 클라이언트가 보낸 URL query parameter
    // ex: /api/articles/daily?date=2025-09-26&page=1&size=10
    const data = await getDailyArticles(req.query);
    res.json({ data });
  } catch (error) {
    next(error);
  }
}

export async function handleWeeklyArticles(req, res, next) {
  try {
    const data = await getWeeklyArticles(req.query);
    res.json({ data });
  } catch (error) {
    next(error);
  }
}

export async function handleSearch(req, res, next) {
  try {
    const data = await getSearchResults(req.query);
    res.json({ data });
  } catch (error) {
    next(error);
  }
}

export async function handleDailySidebar(req, res, next) {
  try {
    const items = await getDailySidebar();
    res.json({ data: items });
  } catch (error) {
    next(error);
  }
}

export async function handleWeeklySidebar(req, res, next) {
  try {
    const items = await getWeeklySidebar();
    res.json({ data: items });
  } catch (error) {
    next(error);
  }
}
// 클라이언트로부터 받은 request query를 `getDailyArticles`로 넘기고 받은 값들을 JSON 형태로 출력
