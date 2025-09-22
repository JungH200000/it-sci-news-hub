/* eslint-disable @next/next/no-img-element */
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  dailyDates,
  weeklyWeeks,
  getDailyArticles,
  getWeeklyArticles,
  searchArticles,
  sidebarMeta,
  searchHints,
} from '../data/mockData';

const TABS = [
  { id: 'daily', label: 'Daily IT/Science' },
  { id: 'weekly', label: 'Weekly SciTech' },
];

const LOAD_SIZE = 10;
const FALLBACK_THUMBNAILS = {
  daily: 'https://placehold.co/640x360/dbeafe/1d4ed8?text=Daily+News',
  weekly: 'https://placehold.co/640x360/0f172a/60a5fa?text=Weekly+Brief',
};

export default function Home() {
  const [activeTab, setActiveTab] = useState('daily');
  const [selectedDate, setSelectedDate] = useState(dailyDates[0]?.value ?? '');
  const [selectedWeek, setSelectedWeek] = useState(weeklyWeeks[0]?.value ?? '');

  const [visibleDailyCount, setVisibleDailyCount] = useState(LOAD_SIZE);
  const [visibleWeeklyCount, setVisibleWeeklyCount] = useState(LOAD_SIZE);
  const [dailyLoading, setDailyLoading] = useState(false);
  const [weeklyLoading, setWeeklyLoading] = useState(false);
  const [focusTargetId, setFocusTargetId] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchState, setSearchState] = useState({
    performed: false,
    results: { daily: [], weekly: [] },
  });
  const [searchLoading, setSearchLoading] = useState(false);
  const [visibleSearchDailyCount, setVisibleSearchDailyCount] = useState(LOAD_SIZE);
  const [visibleSearchWeeklyCount, setVisibleSearchWeeklyCount] = useState(LOAD_SIZE);
  const [searchFocusTargetId, setSearchFocusTargetId] = useState(null);
  const [isCompactLayout, setIsCompactLayout] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const tabRefs = useRef([]);
  const cardRefs = useRef({});
  const searchCardRefs = useRef({});
  const timersRef = useRef([]);
  const searchHeadingRef = useRef(null);

  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer));
      timersRef.current = [];
    };
  }, []);

  useEffect(() => {
    if (focusTargetId && cardRefs.current[focusTargetId]) {
      cardRefs.current[focusTargetId].focus();
      setFocusTargetId(null);
    }
  }, [focusTargetId, visibleDailyCount, visibleWeeklyCount]);

  useEffect(() => {
    if (searchFocusTargetId && searchCardRefs.current[searchFocusTargetId]) {
      searchCardRefs.current[searchFocusTargetId].focus();
      setSearchFocusTargetId(null);
    }
  }, [searchFocusTargetId, visibleSearchDailyCount, visibleSearchWeeklyCount]);

  useEffect(() => {
    setVisibleDailyCount(LOAD_SIZE);
  }, [selectedDate]);

  useEffect(() => {
    setVisibleWeeklyCount(LOAD_SIZE);
  }, [selectedWeek]);

  const dailyArticles = useMemo(() => getDailyArticles(selectedDate), [selectedDate]);
  const weeklyArticles = useMemo(() => getWeeklyArticles(selectedWeek), [selectedWeek]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const mediaQuery = window.matchMedia('(max-width: 1080px)');
    const updateCompact = (event) => {
      setIsCompactLayout(event.matches);
    };

    setIsCompactLayout(mediaQuery.matches);
    mediaQuery.addEventListener('change', updateCompact);

    return () => {
      mediaQuery.removeEventListener('change', updateCompact);
    };
  }, []);

  useEffect(() => {
    if (isCompactLayout) {
      setIsSidebarOpen(false);
    } else {
      setIsSidebarOpen(true);
    }
  }, [isCompactLayout]);

  useEffect(() => {
    if (isCompactLayout) {
      setIsSidebarOpen(false);
    }
  }, [selectedDate, selectedWeek, activeTab, isCompactLayout]);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    const tabIndex = TABS.findIndex((tab) => tab.id === tabId);
    const target = tabRefs.current[tabIndex];
    if (target) {
      target.focus();
    }
  };

  const handleTabKeyDown = (event) => {
    const currentIndex = TABS.findIndex((tab) => tab.id === activeTab);
    if (currentIndex < 0) return;

    let nextIndex = currentIndex;
    if (event.key === 'ArrowRight') {
      nextIndex = (currentIndex + 1) % TABS.length;
      event.preventDefault();
    } else if (event.key === 'ArrowLeft') {
      nextIndex = (currentIndex - 1 + TABS.length) % TABS.length;
      event.preventDefault();
    } else if (event.key === 'Home') {
      nextIndex = 0;
      event.preventDefault();
    } else if (event.key === 'End') {
      nextIndex = TABS.length - 1;
      event.preventDefault();
    }

    if (nextIndex !== currentIndex) {
      const nextTab = TABS[nextIndex];
      setActiveTab(nextTab.id);
      const target = tabRefs.current[nextIndex];
      if (target) target.focus();
    }
  };

  const handleDailyLoadMore = () => {
    if (dailyLoading) return;
    const total = dailyArticles.length;
    if (visibleDailyCount >= total) return;

    setDailyLoading(true);
    const nextVisible = Math.min(visibleDailyCount + LOAD_SIZE, total);
    const focusId = dailyArticles[visibleDailyCount]?.id ?? null;
    const timer = setTimeout(() => {
      setVisibleDailyCount(nextVisible);
      setFocusTargetId(focusId);
      setDailyLoading(false);
    }, 450);
    timersRef.current.push(timer);
  };

  const handleWeeklyLoadMore = () => {
    if (weeklyLoading) return;
    const total = weeklyArticles.length;
    if (visibleWeeklyCount >= total) return;

    setWeeklyLoading(true);
    const nextVisible = Math.min(visibleWeeklyCount + LOAD_SIZE, total);
    const focusId = weeklyArticles[visibleWeeklyCount]?.id ?? null;
    const timer = setTimeout(() => {
      setVisibleWeeklyCount(nextVisible);
      setFocusTargetId(focusId);
      setWeeklyLoading(false);
    }, 450);
    timersRef.current.push(timer);
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setSearchLoading(true);

    const timer = setTimeout(() => {
      const results = searchArticles(searchQuery);
      setSearchState({ performed: true, results });
      setVisibleSearchDailyCount(LOAD_SIZE);
      setVisibleSearchWeeklyCount(LOAD_SIZE);
      setSearchFocusTargetId(null);
      setSearchLoading(false);
      setTimeout(() => {
        focusSearchHeading();
      }, 0);
    }, 420);

    timersRef.current.push(timer);
  };

  const handleSearchLoadMore = (kind) => {
    if (searchLoading) return;
    const list = searchState.results[kind];
    if (!list?.length) return;

    if (kind === 'daily') {
      if (visibleSearchDailyCount >= list.length) return;
      const focusId = list[visibleSearchDailyCount]?.id ?? null;
      const timer = setTimeout(() => {
        setVisibleSearchDailyCount((prev) => Math.min(prev + LOAD_SIZE, list.length));
        setSearchFocusTargetId(focusId);
      }, 360);
      timersRef.current.push(timer);
    } else {
      if (visibleSearchWeeklyCount >= list.length) return;
      const focusId = list[visibleSearchWeeklyCount]?.id ?? null;
      const timer = setTimeout(() => {
        setVisibleSearchWeeklyCount((prev) => Math.min(prev + LOAD_SIZE, list.length));
        setSearchFocusTargetId(focusId);
      }, 360);
      timersRef.current.push(timer);
    }
  };

  const registerCardRef = (id) => (element) => {
    if (element) {
      cardRefs.current[id] = element;
    }
  };

  const registerSearchCardRef = (id) => (element) => {
    if (element) {
      searchCardRefs.current[id] = element;
    }
  };

  const focusSearchHeading = () => {
    if (searchHeadingRef.current) {
      const node = searchHeadingRef.current;
      if (typeof node.focus === 'function') {
        try {
          node.focus({ preventScroll: true });
        } catch (error) {
          node.focus();
        }
      }
      node.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const renderArticles = (articles, visibleCount, isWeekly = false, registerRef) => {
    return (
      <div className="card-grid">
        {articles.slice(0, visibleCount).map((article) => (
          <article
            key={article.id}
            ref={registerRef(article.id)}
            className="article-card"
            tabIndex={-1}
          >
            <img
              src={resolveThumbnail(article, isWeekly)}
              alt={
                article.thumbnail
                  ? '기사 썸네일'
                  : isWeekly
                    ? '주간 뉴스 기본 썸네일'
                    : '일일 뉴스 기본 썸네일'
              }
              className="article-card__thumbnail"
              loading="lazy"
            />
            <header className="article-card__meta">
              <span>{article.source}</span>
              {isWeekly && article.periodLabel ? <span>{article.periodLabel}</span> : null}
              {!isWeekly && article.publishedAt ? (
                <span>{formatKST(article.publishedAt)}</span>
              ) : null}
              <span className="article-card__category">{article.category}</span>
            </header>
            <h3 className="article-card__title">
              <a href={article.link} target="_blank" rel="noreferrer">
                {article.title}
              </a>
            </h3>
            <p className="article-card__summary">{article.summary}</p>
          </article>
        ))}
      </div>
    );
  };

  const searchHasResults = searchState.results.daily.length + searchState.results.weekly.length > 0;
  const sidebarEntries = activeTab === 'daily' ? dailyDates : weeklyWeeks;
  const selectedValue = activeTab === 'daily' ? selectedDate : selectedWeek;
  const selectedEntry = sidebarEntries.find((entry) => entry.value === selectedValue);

  return (
    <main>
      <header className="header">
        <div className="header__brand" aria-label="IT/Science News Hub">
          <div className="header__brand-icon" aria-hidden="true">
            <img src="/science_logo.png" alt="" width={40} height={40} />
          </div>
          <span>IT/Science News Hub</span>
        </div>

        <div className="tabs">
          <div
            className="tablist"
            role="tablist"
            aria-label="뉴스 탭 선택"
            onKeyDown={handleTabKeyDown}
          >
            {TABS.map((tab, index) => (
              <button
                key={tab.id}
                role="tab"
                ref={(element) => {
                  tabRefs.current[index] = element;
                }}
                id={`tab-${tab.id}`}
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                className="tab"
                tabIndex={activeTab === tab.id ? 0 : -1}
                onClick={() => handleTabChange(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <form className="search-form" onSubmit={handleSearchSubmit} role="search">
          <label htmlFor="search-input" className="sr-only">
            키워드 검색
          </label>
          <input
            id="search-input"
            className="search-input"
            type="search"
            placeholder={`예: ${searchHints.join(', ')}`}
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
          <button type="submit" className="search-button" disabled={searchLoading}>
            {searchLoading ? 'Searching…' : 'Search'}
          </button>
        </form>
      </header>

      <div className="layout">
        <section
          className="content"
          id={`panel-${activeTab}`}
          role="tabpanel"
          aria-labelledby={`tab-${activeTab}`}
        >
          <h2 className="section-heading">
            {activeTab === 'daily' ? 'Daily Headlines' : 'Weekly Spotlight'}
          </h2>

          {activeTab === 'daily'
            ? renderArticles(dailyArticles, visibleDailyCount, false, registerCardRef)
            : renderArticles(weeklyArticles, visibleWeeklyCount, true, registerCardRef)}

          {activeTab === 'daily' ? (
            <LoadMoreSection
              total={dailyArticles.length}
              visible={visibleDailyCount}
              isLoading={dailyLoading}
              onLoadMore={handleDailyLoadMore}
            />
          ) : (
            <LoadMoreSection
              total={weeklyArticles.length}
              visible={visibleWeeklyCount}
              isLoading={weeklyLoading}
              onLoadMore={handleWeeklyLoadMore}
            />
          )}
        </section>

        <aside
          className={`sidebar${isCompactLayout ? ' sidebar--compact' : ''}`}
          aria-label={activeTab === 'daily' ? 'Daily 날짜 선택' : 'Weekly 주차 선택'}
        >
          <h3 className="sidebar__title">{activeTab === 'daily' ? '최근 14일' : '최근 8주'}</h3>
          <p className="alert">{sidebarMeta[activeTab]}</p>
          {isCompactLayout ? (
            <div className="sidebar__collapsible">
              <button
                type="button"
                className="sidebar__toggle"
                aria-expanded={isSidebarOpen ? 'true' : 'false'}
                onClick={() => setIsSidebarOpen((prev) => !prev)}
              >
                <span className="sidebar__toggle-label">
                  {selectedEntry ? selectedEntry.label : '항목 선택'}
                </span>
                {selectedEntry?.isNew ? <span className="badge badge--inline">New</span> : null}
              </button>
              <div className="sidebar__panel" hidden={!isSidebarOpen}>
                <ul className="sidebar__list sidebar__list--compact">
                  {sidebarEntries.map((entry) => {
                    const isSelected = selectedValue === entry.value;
                    return (
                      <li key={entry.value}>
                        <button
                          type="button"
                          className="sidebar__button"
                          aria-pressed={isSelected}
                          onClick={() => {
                            if (activeTab === 'daily') {
                              setSelectedDate(entry.value);
                            } else {
                              setSelectedWeek(entry.value);
                            }
                            setIsSidebarOpen(false);
                          }}
                        >
                          <span>{entry.label}</span>
                          {entry.isNew ? <span className="badge">New</span> : null}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>
          ) : (
            <ul className="sidebar__list">
              {sidebarEntries.map((entry) => {
                const isSelected = selectedValue === entry.value;

                return (
                  <li key={entry.value}>
                    <button
                      type="button"
                      className="sidebar__button"
                      aria-pressed={isSelected}
                      onClick={() => {
                        if (activeTab === 'daily') {
                          setSelectedDate(entry.value);
                        } else {
                          setSelectedWeek(entry.value);
                        }
                      }}
                    >
                      <span>{entry.label}</span>
                      {entry.isNew ? <span className="badge">New</span> : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </aside>
      </div>

      <section className="search-results" aria-live="polite">
        <div className="search-results__header">
          <h2 className="section-heading" ref={searchHeadingRef} tabIndex={-1}>
            Search Results
          </h2>
          {!searchState.performed ? (
            <span className="text-secondary">키워드를 입력하고 검색하세요.</span>
          ) : null}
        </div>

        {searchState.performed && !searchHasResults && !searchLoading ? (
          <p className="alert" role="status">
            No results found
          </p>
        ) : null}

        {searchLoading ? (
          <p className="alert" role="status">
            검색 중입니다…
          </p>
        ) : null}

        {searchState.results.daily.length ? (
          <SearchSection
            heading="Daily (최근 14일)"
            articles={searchState.results.daily}
            visibleCount={visibleSearchDailyCount}
            onLoadMore={() => handleSearchLoadMore('daily')}
            isLoading={searchLoading}
            registerRef={registerSearchCardRef}
          />
        ) : null}

        {searchState.results.weekly.length ? (
          <SearchSection
            heading="Weekly"
            articles={searchState.results.weekly}
            visibleCount={visibleSearchWeeklyCount}
            onLoadMore={() => handleSearchLoadMore('weekly')}
            isLoading={searchLoading}
            registerRef={registerSearchCardRef}
            isWeekly
          />
        ) : null}
      </section>
    </main>
  );
}

function LoadMoreSection({ total, visible, isLoading, onLoadMore }) {
  const hasMore = visible < total;
  return (
    <div>
      {hasMore ? (
        <button
          type="button"
          className="load-more"
          onClick={onLoadMore}
          disabled={isLoading}
          aria-busy={isLoading ? 'true' : 'false'}
        >
          {isLoading ? 'Loading…' : 'Load More'}
        </button>
      ) : (
        <div className="status-line" role="status">
          No more results
        </div>
      )}
    </div>
  );
}

function SearchSection({
  heading,
  articles,
  visibleCount,
  onLoadMore,
  isLoading,
  registerRef,
  isWeekly,
}) {
  const hasMore = visibleCount < articles.length;
  return (
    <section>
      <h3 className="section-heading">{heading}</h3>
      <div className="card-grid">
        {articles.slice(0, visibleCount).map((article) => (
          <article
            key={`search-${article.id}`}
            ref={registerRef(`search-${article.id}`)}
            className="article-card"
            tabIndex={-1}
          >
            <img
              src={resolveThumbnail(article, isWeekly)}
              alt={
                article.thumbnail
                  ? '검색 결과 썸네일'
                  : isWeekly
                    ? '주간 검색 기본 썸네일'
                    : '일일 검색 기본 썸네일'
              }
              className="article-card__thumbnail"
              loading="lazy"
            />
            <header className="article-card__meta">
              <span>{article.source}</span>
              {isWeekly && article.periodLabel ? <span>{article.periodLabel}</span> : null}
              {!isWeekly && article.publishedAt ? (
                <span>{formatKST(article.publishedAt)}</span>
              ) : null}
              <span className="article-card__category">{article.category}</span>
            </header>
            <h4 className="article-card__title">
              <a href={article.link} target="_blank" rel="noreferrer">
                {article.title}
              </a>
            </h4>
            <p className="article-card__summary">{article.summary}</p>
          </article>
        ))}
      </div>
      {hasMore ? (
        <button
          type="button"
          className="load-more"
          onClick={onLoadMore}
          disabled={isLoading}
          aria-busy={isLoading ? 'true' : 'false'}
        >
          {isLoading ? 'Loading…' : 'Load More'}
        </button>
      ) : (
        <div className="status-line" role="status">
          No more results
        </div>
      )}
    </section>
  );
}

function formatKST(isoString) {
  if (!isoString) return '';
  try {
    const date = new Date(isoString);
    return date.toLocaleString('ko-KR', {
      timeZone: 'Asia/Seoul',
      hour12: false,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return isoString;
  }
}

function resolveThumbnail(article, isWeekly) {
  if (article.thumbnail && article.thumbnail.trim()) {
    return article.thumbnail;
  }

  return isWeekly ? FALLBACK_THUMBNAILS.weekly : FALLBACK_THUMBNAILS.daily;
}
