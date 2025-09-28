// 이 파일은 HTTP 상태 코드를 담은 커스텀 에러 객체와 자주 쓰는 상태 코드를 빠르게 만들 수 있는 도우미 함수를 제공합니다.

export class HttpError extends Error {
  constructor(status, message, expose = true) {
    super(message);
    this.name = this.constructor.name;
    this.status = status;
    this.expose = expose;
  }
}

export const badRequest = (message) => new HttpError(400, message);
export const notFound = (message) => new HttpError(404, message);
export const serviceUnavailable = (message) => new HttpError(503, message);
