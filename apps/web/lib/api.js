const DEFAULT_BASE_URL = 'http://localhost:4000/api';

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '');

export async function apiGet(path, params) {
  const url = new URL(`${baseUrl}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const response = await fetch(url.toString());
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      message = payload?.error?.message || message;
    } catch (error) {
      // ignore JSON parse errors
    }
    throw new Error(message);
  }

  return response.json();
}

export { baseUrl as API_BASE_URL };
