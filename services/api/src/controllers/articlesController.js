import {
  getDailyArticles,
  getWeeklyArticles,
  getSearchResults,
  getDailySidebar,
  getWeeklySidebar,
} from '../services/articlesService.js';

export async function handleDailyArticles(req, res, next) {
  try {
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
