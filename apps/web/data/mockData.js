const dailyDateEntries = [
  { value: '2025-09-14', label: '2025-09-14 (일)', isNew: true },
  { value: '2025-09-13', label: '2025-09-13 (토)' },
  { value: '2025-09-12', label: '2025-09-12 (금)' },
  { value: '2025-09-11', label: '2025-09-11 (목)' },
  { value: '2025-09-10', label: '2025-09-10 (수)' },
  { value: '2025-09-09', label: '2025-09-09 (화)' },
  { value: '2025-09-08', label: '2025-09-08 (월)' },
  { value: '2025-09-07', label: '2025-09-07 (일)' },
  { value: '2025-09-06', label: '2025-09-06 (토)' },
  { value: '2025-09-05', label: '2025-09-05 (금)' },
  { value: '2025-09-04', label: '2025-09-04 (목)' },
  { value: '2025-09-03', label: '2025-09-03 (수)' },
  { value: '2025-09-02', label: '2025-09-02 (화)' },
  { value: '2025-09-01', label: '2025-09-01 (월)' }
];

const weeklyWeekEntries = [
  { value: '2025-09-3', label: '2025년 9월 3주차', isNew: true },
  { value: '2025-09-2', label: '2025년 9월 2주차' },
  { value: '2025-09-1', label: '2025년 9월 1주차' },
  { value: '2025-08-4', label: '2025년 8월 4주차' },
  { value: '2025-08-3', label: '2025년 8월 3주차' },
  { value: '2025-08-2', label: '2025년 8월 2주차' },
  { value: '2025-08-1', label: '2025년 8월 1주차' },
  { value: '2025-07-4', label: '2025년 7월 4주차' }
];

const categories = ['AI', '보안', '반도체', '로봇', '생명과학', 'IT/과학', 'IT/기술', '기타'];

const dailyArticlesByDate = {};
const weeklyArticlesByWeek = {};
const dailySearchCorpus = [];
const weeklySearchCorpus = [];

function createDailyArticles(dateValue, index) {
  const items = Array.from({ length: 12 }, (_, idx) => {
    const category = categories[(index + idx) % categories.length];
    const summary = `${category} 분야에서 주목할 만한 흐름을 담은 일일 뉴스. ${idx + 1}번째 하이라이트.`;
    const id = `daily-${dateValue}-${idx + 1}`;
    const publishedHour = String(6 + (idx % 4)).padStart(2, '0');
    const publishedMinute = String(5 + idx).padStart(2, '0');
    const thumbnail = idx % 4 === 0 ? null : `https://placehold.co/640x360/1d4ed8/ffffff?text=${encodeURIComponent(category)}`;

    const article = {
      id,
      title: `Daily Insight ${index + 1}-${idx + 1}: ${category} 트렌드`,
      summary,
      source: '한국경제 IT',
      link: `https://example.com/daily/${dateValue}/${idx + 1}`,
      publishedAt: `${dateValue}T${publishedHour}:${publishedMinute}:00+09:00`,
      category,
      thumbnail
    };

    dailySearchCorpus.push(article);
    return article;
  });

  dailyArticlesByDate[dateValue] = items;
}

dailyDateEntries.forEach((entry, index) => createDailyArticles(entry.value, index));

function createWeeklyArticles(weekValue, index) {
  const items = Array.from({ length: 12 }, (_, idx) => {
    const category = idx % 3 === 0 ? '과학기술' : categories[(index + idx) % categories.length];
    const summary = `${category} 관점에서 정리한 주간 R&D 브리프. ${idx + 1}번째 주요 이슈.`;
    const id = `weekly-${weekValue}-${idx + 1}`;
    const article = {
      id,
      title: `Weekly Spotlight ${index + 1}-${idx + 1}: ${category} 초점`,
      summary,
      source: 'scienceON',
      link: `https://example.com/weekly/${weekValue}/${idx + 1}`,
      category,
      periodLabel: weeklyWeekEntries[index].label,
      thumbnail: idx % 5 === 0 ? null : `https://placehold.co/640x360/0f172a/FFFFFF?text=${encodeURIComponent(category)}`
    };

    weeklySearchCorpus.push(article);
    return article;
  });

  weeklyArticlesByWeek[weekValue] = items;
}

weeklyWeekEntries.forEach((entry, index) => createWeeklyArticles(entry.value, index));

export const dailyDates = dailyDateEntries;
export const weeklyWeeks = weeklyWeekEntries;

export function getDailyArticles(dateValue) {
  return dailyArticlesByDate[dateValue] ?? [];
}

export function getWeeklyArticles(weekValue) {
  return weeklyArticlesByWeek[weekValue] ?? [];
}

export function searchArticles(query) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return { daily: [], weekly: [] };
  }

  const toText = (value) => (value ?? '').toLowerCase();
  const sanitizeTitle = (title) =>
    toText(title)
      .replace(/daily insight\s*\d+-\d+:\s*/g, '')
      .replace(/weekly spotlight\s*\d+-\d+:\s*/g, '');

  const matchesAny = (parts) => parts.some((part) => part && part.includes(normalized));

  const matchesDaily = (item) =>
    matchesAny([
      sanitizeTitle(item.title),
      toText(item.summary),
      toText(item.category),
      toText(item.source),
    ]);

  const matchesWeekly = (item) =>
    matchesAny([
      sanitizeTitle(item.title),
      toText(item.summary),
      toText(item.category),
      toText(item.periodLabel),
      toText(item.source),
    ]);

  return {
    daily: dailySearchCorpus.filter(matchesDaily).slice(0, 40),
    weekly: weeklySearchCorpus.filter(matchesWeekly).slice(0, 40),
  };
}

export const sidebarMeta = {
  daily: '최근 14일 동안의 주요 IT/과학 뉴스를 선택하세요.',
  weekly: '최근 8주 트렌드 리포트를 둘러보세요.'
};

export const searchHints = ['AI', '반도체', '보안', '양자', '우주', '에너지'];
