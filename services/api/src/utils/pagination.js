// 이 파일은 페이지 번호와 크기를 안전하게 숫자로 바꿔 주고, 어떤 위치에서 데이터를 가져올지 오프셋을 계산해 주는 보조 함수입니다.

export function parsePagination(params, defaults) {
  const page = clampPositiveInt(params.page, 1); // page >= 1인 정수면 그대로 사용, 아니면 기본값 1
  const size = clampPositiveInt(params.size, defaults.defaultSize); // size >= 1인 정수면 그대로 사용, 아니면 defaultSize
  const limit = Math.min(size, defaults.maxSize); // 요청 크기가 너무 크면 maxSize까지 허용
  const offset = (page - 1) * limit; // 몇 번째 데이터부터 가져올지 계산
  return { page, size: limit, offset };
}

function clampPositiveInt(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isFinite(parsed) && parsed > 0) {
    return parsed;
  }
  return fallback;
}
