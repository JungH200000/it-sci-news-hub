// 이 파일은 개별 기능별 라우터를 묶어서 `/api` 경로에 한 번에 연결할 준비를 합니다.

import { Router } from 'express';
import articlesRoutes from './articlesRoutes.js';

const api = Router();

api.use('/', articlesRoutes);

export default api;
