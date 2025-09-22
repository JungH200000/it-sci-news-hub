export function parsePagination(params, defaults) {
  const page = clampPositiveInt(params.page, 1);
  const size = clampPositiveInt(params.size, defaults.defaultSize);
  const limit = Math.min(size, defaults.maxSize);
  const offset = (page - 1) * limit;
  return { page, size: limit, offset };
}

function clampPositiveInt(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isFinite(parsed) && parsed > 0) {
    return parsed;
  }
  return fallback;
}
