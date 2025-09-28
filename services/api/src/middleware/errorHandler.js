// 이 파일은 존재하지 않는 경로를 잡아내고 Express에서 발생한 에러를 공통 형식(JSON)으로 응답하는 미들웨어입니다.

import { HttpError } from '../utils/httpErrors.js';

export const notFoundHandler = (req, res, next) => {
  next(new HttpError(404, `Route ${req.method} ${req.originalUrl} not found`));
};

// eslint-disable-next-line no-unused-vars
export const errorHandler = (err, req, res, next) => {
  const status = err instanceof HttpError ? err.status : 500;
  const expose = err instanceof HttpError ? err.expose : false;
  const message = expose ? err.message : 'Internal Server Error';

  if (status >= 500) {
    req.log?.error({ err }, 'Unhandled error');
  }

  res.status(status).json({
    error: {
      message,
      status,
    },
  });
};
