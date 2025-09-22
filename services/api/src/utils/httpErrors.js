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
