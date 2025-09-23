/* eslint-disable @next/next/no-img-element */
export default function ArticleCard({ article, isWeekly = false, registerRef }) {
  if (!article) return null;
  const { id, title, summary, link, source, category, thumbnail, period_label, published_at, date, week } = article;
  const metaDate = isWeekly ? (period_label || week) : formatDateTime(published_at || date);
  return (
    <article ref={registerRef ? registerRef(id) : null} className="article-card" tabIndex={-1}>
      <img
        src={resolveThumbnail(thumbnail, isWeekly)}
        alt={isWeekly ? '주간 뉴스 썸네일' : '일일 뉴스 썸네일'}
        className="article-card__thumbnail"
        loading="lazy"
      />
      <header className="article-card__meta">
        <span>{source}</span>
        {metaDate ? <span>{metaDate}</span> : null}
        {category ? <span className="article-card__category">{category}</span> : null}
      </header>
      <h3 className="article-card__title">
        <a href={link} target="_blank" rel="noreferrer">
          {title}
        </a>
      </h3>
      {summary ? <p className="article-card__summary">{summary}</p> : <p className="article-card__summary">요약 없음</p>}
    </article>
  );
}

function resolveThumbnail(thumbnail, isWeekly) {
  if (thumbnail) return thumbnail;
  return isWeekly
    ? 'https://placehold.co/640x360/0f172a/60a5fa?text=Weekly+Brief'
    : 'https://placehold.co/640x360/dbeafe/1d4ed8?text=Daily+News';
}

function formatDateTime(value) {
  if (!value) return null;
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return value;
  }
}
