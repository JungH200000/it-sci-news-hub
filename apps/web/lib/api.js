const DEFAULT_BASE_URL = 'http://localhost:4000/api';

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '');

export async function apiGet(path, params) {
  const url = new URL(`${baseUrl}${path}`);
  if (params) {
    // params 객체를 [[key, value], [key, value], ...] 배열로 변경
    // 예시 [[date, 2025-09-29], [page, 1], ...]
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        // URL의 쿼리스트링에 key=value 설정
        // set은 같은 키가 존재할 경우 덮어씀
        url.searchParams.set(key, String(value));
        // 결과: http://localhost:4000/api/articles/daily?date=2025-09-29&page=1&...
      }
    });
  }

  // 브라우저의 fetch로 네트워크 요청을 보냄
  const response = await fetch(url.toString());

  // HTTP 상태 코드가 200~299가 아니면 error 취급
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

  // 성공(2xx)인 경우 response body를 JSON으로 파싱해서 반환
  return response.json();
}

export { baseUrl as API_BASE_URL };
