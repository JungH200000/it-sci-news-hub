import { Router } from 'express';
import articlesRoutes from './articlesRoutes.js';

const api = Router();

api.use('/', articlesRoutes);

export default api;
