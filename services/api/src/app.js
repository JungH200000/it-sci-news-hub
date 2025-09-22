import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import pinoHttp from 'pino-http';
import swaggerUi from 'swagger-ui-express';
import YAML from 'yaml';

import { config } from './config.js';
import apiRoutes from './routes/index.js';
import { notFoundHandler, errorHandler } from './middleware/errorHandler.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const openApiPath = path.resolve(__dirname, '../../docs/openapi.yaml');
let openApiDocument = null;

try {
  const file = fs.readFileSync(openApiPath, 'utf8');
  openApiDocument = YAML.parse(file);
} catch (error) {
  // eslint-disable-next-line no-console
  console.warn('Failed to load OpenAPI document:', error.message);
}

export function createApp() {
  const app = express();

  app.use(pinoHttp());
  app.use(helmet());
  app.use(cors());
  app.use(compression());
  app.use(express.json({ limit: '1mb' }));

  app.use(
    rateLimit({
      windowMs: config.requestRate.windowMs,
      max: config.requestRate.max,
      standardHeaders: true,
      legacyHeaders: false,
    })
  );

  app.get('/healthz', (req, res) => {
    res.set('Cache-Control', 'no-store');
    res.status(200).json({ ok: true, service: 'api', uptime: process.uptime() });
  });

  app.use('/api', apiRoutes);
  if (openApiDocument) {
    app.use('/docs', swaggerUi.serve, swaggerUi.setup(openApiDocument));
  }

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}
