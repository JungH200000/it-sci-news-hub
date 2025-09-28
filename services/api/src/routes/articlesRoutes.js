// 이 파일은 기사 관련 GET 엔드포인트를 정의하는 라우터입니다.
// Express Router를 만들어 각 URL과 컨트롤러 함수를 연결합니다.

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
