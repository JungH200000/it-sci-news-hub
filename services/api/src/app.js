// 이 파일은 Express 앱의 기본 설정을 모아둔 곳입니다. 헬멧, CORS, 압축, 요청 제한 같은 공통 보호 장치를 켜고 API 라우트를 연결합니다.
// OpenAPI 문서를 `/docs`에서 볼 수 있게 하고, 마지막에 공통 에러 처리 미들웨어를 붙입니다.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import pino from 'pino';
import pinoHttp from 'pino-http';
import swaggerUi from 'swagger-ui-express';
import YAML from 'yaml';

import { config } from './config.js';
import apiRoutes from './routes/index.js';
import { notFoundHandler, errorHandler } from './middleware/errorHandler.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const openApiPath = path.resolve(__dirname, '../../../docs/openapi.yaml');
let openApiDocument = null;

try {
  const file = fs.readFileSync(openApiPath, 'utf8');
  openApiDocument = YAML.parse(file);
} catch (error) {
  // eslint-disable-next-line no-console
  console.warn('Failed to load OpenAPI document:', error.message);
}

const pinoLogger = pino({
  level: config.logging.level,
  transport: config.logging.pretty
    ? {
        target: 'pino-pretty',
        options: {
          translateTime: 'SYS:standard',
          ignore: 'pid,hostname',
        },
      }
    : undefined,
});

export function createApp() {
  const app = express();

  // req/res log를 남기는 미들웨어(pino-http) 연결
  app.use(
    pinoHttp({
      logger: pinoLogger,
      customLogLevel: (req, res, err) => {
        if (req.url === '/healthz') return 'silent'; // `/healthz`는 log를 찍지 않음
        if (err || res.statusCode >= 500) return 'error'; // 5xx는 `error`
        if (res.statusCode >= 400) return 'warn'; // 4xx는 `warn`
        return config.logging.level === 'silent' ? 'silent' : 'info';
      },
    })
  );

  // CORS 허용 도메인
  const allowlist = [
    process.env.ALLOWED_ORIGINS,
    'http://localhost:3000', // 로컬 개발용
  ];
  // 허용 도메인이 아니면 error - blocked
  const corsOptions = {
    origin: function (origin, callback) {
      if (!origin || allowlist.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error('CORS blocked: ' + origin));
      }
    },
  };

  // 위에서 정의한 CORS 미들웨어 활성화
  app.use(cors(corsOptions));
  // 보안 헤더 자동으로 설정(Helmet) => XSS, 클릭재킹 등 방어
  app.use(helmet());
  // response 압축 : 네트워크 트래픽 절감 -> 응답 속도 향상시킴
  app.use(compression());
  // JSON body parser : request 본문을 req.body에 파싱. 단, 1MB 제한
  app.use(express.json({ limit: '1mb' }));

  // 요청 속도 제한 : `windowMs`동안 `max`회까지만 허용
  app.use(
    rateLimit({
      windowMs: config.requestRate.windowMs,
      max: config.requestRate.max,
      standardHeaders: true,
      legacyHeaders: false,
    })
  );

  // 서버 연결 상태 확인??
  app.get('/healthz', (req, res) => {
    res.set('Cache-Control', 'no-store');
    res.status(200).json({ ok: true, service: 'api', uptime: process.uptime() });
  });

  // 모든 API 라우트를 `/api` 아래로 연결
  app.use('/api', apiRoutes);
  // `/api` 접두어를 붙여라 -> `routes/index.js`가 관리하는 모든 경로 앞에는 자동으로 `/api`가 붙는다.
  // 즉, `/articles/daily` -> `/api/articles/daily`가 완성됨

  if (openApiDocument) {
    app.use('/docs', swaggerUi.serve, swaggerUi.setup(openApiDocument));
  }

  // 404 처리 미들웨어
  app.use(notFoundHandler);
  // 공통 에러 처리 미들웨어
  app.use(errorHandler);

  // 완성된 Express 앱 객체 반환
  return app;
}
