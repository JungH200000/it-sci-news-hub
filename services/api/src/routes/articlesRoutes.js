import { Router } from 'express';
import {
  handleDailyArticles,
  handleWeeklyArticles,
  handleSearch,
  handleDailySidebar,
  handleWeeklySidebar,
} from '../controllers/articlesController.js';

const router = Router();

router.get('/articles/daily', handleDailyArticles);
router.get('/articles/weekly', handleWeeklyArticles);
router.get('/articles/sidebar/daily', handleDailySidebar);
router.get('/articles/sidebar/weekly', handleWeeklySidebar);
router.get('/search', handleSearch);

export default router;
