// 이 파일은 개별 기능별 라우터를 묶어서 `/api` 경로에 한 번에 연결할 준비를 합니다.

import { Router } from 'express';
import articlesRoutes from './articlesRoutes.js';

/* ===== 라우터 묶음 ===== */
const api = Router();

// `/(루트)` 경로 밑에 `articlesRoutes`에서 정의한 경로들을 붙여라.
api.use('/', articlesRoutes); // 여전히 `/articles/daily` 로 동작

export default api;
