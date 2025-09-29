import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ArticleCard from '../components/ArticleCard';
import { useDailySidebar } from '../hooks/useDailySidebar';
import { useWeeklySidebar } from '../hooks/useWeeklySidebar';
import { useDailyArticles } from '../hooks/useDailyArticles';
import { useWeeklyArticles } from '../hooks/useWeeklyArticles';
import { apiGet } from '../lib/api';
import { sidebarMeta, searchHints } from '../data/mockData';

const LOAD_SIZE = 10;

export default function Home() {
  const [activeTab, setActiveTab] = useState('daily');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedWeek, setSelectedWeek] = useState('');
  const [isCompactLayout, setIsCompactLayout] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const {
    items: dailySidebarItems,
    loading: dailySidebarLoading,
    error: dailySidebarError,
  } = useDailySidebar();
  const {
    items: weeklySidebarItems,
    loading: weeklySidebarLoading,
    error: weeklySidebarError,
  } = useWeeklySidebar();

  useEffect(() => {
    if (!selectedDate && dailySidebarItems.length) {
      setSelectedDate(dailySidebarItems[0].value);
    }
  }, [dailySidebarItems, selectedDate]);

  useEffect(() => {
    if (!selectedWeek && weeklySidebarItems.length) {
      setSelectedWeek(weeklySidebarItems[0].value);
    }
  }, [weeklySidebarItems, selectedWeek]);

  const {
    items: dailyArticles,
    hasMore: dailyHasMore,
    loading: dailyLoading,
    loadingMore: dailyLoadingMore,
    error: dailyError,
    loadMore: loadMoreDaily,
  } = useDailyArticles(selectedDate);

  const {
    items: weeklyArticles,
    hasMore: weeklyHasMore,
    loading: weeklyLoading,
    loadingMore: weeklyLoadingMore,
    error: weeklyError,
    loadMore: loadMoreWeekly,
  } = useWeeklyArticles(selectedWeek);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState({ daily: [], weekly: [] });
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [visibleSearchDailyCount, setVisibleSearchDailyCount] = useState(LOAD_SIZE);
  const [visibleSearchWeeklyCount, setVisibleSearchWeeklyCount] = useState(LOAD_SIZE);

  const tabRefs = useRef([]);
  const cardRefs = useRef({});
  const searchCardRefs = useRef({});
  const searchHeadingRef = useRef(null);

  const [focusTargetId, setFocusTargetId] = useState(null);
  const [searchFocusTargetId, setSearchFocusTargetId] = useState(null);

  useEffect(() => {
    if (focusTargetId && cardRefs.current[focusTargetId]) {
      cardRefs.current[focusTargetId].focus();
      setFocusTargetId(null);
    }
  }, [focusTargetId, dailyArticles, weeklyArticles]);

  useEffect(() => {
    if (searchFocusTargetId && searchCardRefs.current[searchFocusTargetId]) {
      searchCardRefs.current[searchFocusTargetId].focus();
      setSearchFocusTargetId(null);
    }
  }, [searchFocusTargetId, visibleSearchDailyCount, visibleSearchWeeklyCount]);

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

  const handleDailyLoadMore = useCallback(async () => {
    const focusId = await loadMoreDaily();
    if (focusId) {
      setFocusTargetId(focusId);
    }
  }, [loadMoreDaily]);

  const handleWeeklyLoadMore = useCallback(async () => {
    const focusId = await loadMoreWeekly();
    if (focusId) {
      setFocusTargetId(focusId);
    }
  }, [loadMoreWeekly]);

  const handleSearchSubmit = async (event) => {
    event.preventDefault();
    // searchQuery: 입력창 값
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setSearchResults({ daily: [], weekly: [] });
      setSearchPerformed(false);
      setSearchError(null);
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    setSearchPerformed(false);
    try {
      const result = await apiGet('/search', { q: trimmed });
      const payload = result?.data || {};
      setSearchResults({
        daily: Array.isArray(payload.results?.daily) ? payload.results.daily : [],
        weekly: Array.isArray(payload.results?.weekly) ? payload.results.weekly : [],
      });
      setVisibleSearchDailyCount(LOAD_SIZE);
      setVisibleSearchWeeklyCount(LOAD_SIZE);
      setSearchPerformed(true);
      focusSearchHeading();
    } catch (err) {
      setSearchResults({ daily: [], weekly: [] });
      setSearchError(err.message || '검색에 실패했습니다.');
      setSearchPerformed(true);
    } finally {
      setSearchLoading(false);
    }
  };

  const focusSearchHeading = useCallback(() => {
    if (searchHeadingRef.current) {
      const node = searchHeadingRef.current;
      try {
        node.focus({ preventScroll: true });
      } catch (error) {
        node.focus();
      }
      node.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  const handleSearchLoadMore = (kind) => {
    if (searchLoading) return;
    if (kind === 'daily') {
      if (visibleSearchDailyCount >= searchResults.daily.length) return;
      const next = Math.min(visibleSearchDailyCount + LOAD_SIZE, searchResults.daily.length);
      const focusId = searchResults.daily[visibleSearchDailyCount]?.id ?? null;
      setVisibleSearchDailyCount(next);
      if (focusId) setSearchFocusTargetId(`search-${focusId}`);
    } else {
      if (visibleSearchWeeklyCount >= searchResults.weekly.length) return;
      const next = Math.min(visibleSearchWeeklyCount + LOAD_SIZE, searchResults.weekly.length);
      const focusId = searchResults.weekly[visibleSearchWeeklyCount]?.id ?? null;
      setVisibleSearchWeeklyCount(next);
      if (focusId) setSearchFocusTargetId(`search-${focusId}`);
    }
  };

  const registerCardRef = useCallback(
    (id) => (element) => {
      if (element) {
        cardRefs.current[id] = element;
      }
    },
    []
  );

  const registerSearchCardRef = useCallback(
    (id) => (element) => {
      if (element) {
        searchCardRefs.current[id] = element;
      }
    },
    []
  );

  const activeArticles = activeTab === 'daily' ? dailyArticles : weeklyArticles;
  const activeLoading = activeTab === 'daily' ? dailyLoading : weeklyLoading;
  const activeLoadingMore = activeTab === 'daily' ? dailyLoadingMore : weeklyLoadingMore;
  const activeError = activeTab === 'daily' ? dailyError : weeklyError;
  const canLoadMore = activeTab === 'daily' ? dailyHasMore : weeklyHasMore;
  const onLoadMore = activeTab === 'daily' ? handleDailyLoadMore : handleWeeklyLoadMore;

  const searchHasResults = useMemo(() => {
    return searchResults.daily.length + searchResults.weekly.length > 0;
  }, [searchResults]);

  return (
    <main>
      <header className="header">
        <div className="header__brand" aria-label="IT/Science News Hub">
          <div className="header__brand-icon" aria-hidden="true">
            Δ
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

          {activeError ? (
            <p className="alert" role="status">
              {activeError}
            </p>
          ) : null}

          {activeLoading && !activeArticles.length ? (
            <p className="status-line" role="status">
              Loading…
            </p>
          ) : null}

          {!activeLoading && !activeArticles.length && !activeError ? (
            <p className="status-line" role="status">
              No results found
            </p>
          ) : null}

          <div className="card-grid">
            {activeArticles.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                isWeekly={activeTab === 'weekly'}
                registerRef={registerCardRef}
              />
            ))}
          </div>

          {canLoadMore ? (
            <button
              type="button"
              className="load-more"
              onClick={onLoadMore}
              disabled={activeLoadingMore}
              aria-busy={activeLoadingMore ? 'true' : 'false'}
            >
              {activeLoadingMore ? 'Loading…' : 'Load More'}
            </button>
          ) : !activeLoading && activeArticles.length ? (
            <div className="status-line" role="status">
              No more results
            </div>
          ) : null}
        </section>

        <aside
          className={`sidebar${isCompactLayout ? ' sidebar--compact' : ''}`}
          aria-label={activeTab === 'daily' ? 'Daily 날짜 선택' : 'Weekly 주차 선택'}
        >
          <h3 className="sidebar__title">{activeTab === 'daily' ? '최근 14일' : '최근 8주'}</h3>
          <p className="alert">{sidebarMeta[activeTab]}</p>

          {activeTab === 'daily' ? (
            <SidebarList
              items={dailySidebarItems}
              loading={dailySidebarLoading}
              error={dailySidebarError}
              selected={selectedDate}
              onSelect={(value) => setSelectedDate(value)}
              isCompact={isCompactLayout}
              isOpen={isSidebarOpen}
              onToggle={() => setIsSidebarOpen((prev) => !prev)}
            />
          ) : (
            <SidebarList
              items={weeklySidebarItems}
              loading={weeklySidebarLoading}
              error={weeklySidebarError}
              selected={selectedWeek}
              onSelect={(value) => setSelectedWeek(value)}
              isCompact={isCompactLayout}
              isOpen={isSidebarOpen}
              onToggle={() => setIsSidebarOpen((prev) => !prev)}
            />
          )}
        </aside>
      </div>

      <section className="search-results" aria-live="polite">
        <div className="search-results__header">
          <h2 className="section-heading" ref={searchHeadingRef} tabIndex={-1}>
            Search Results
          </h2>
          {!searchPerformed ? (
            <span className="text-secondary">키워드를 입력하고 검색하세요.</span>
          ) : null}
        </div>

        {searchError ? (
          <p className="alert" role="status">
            {searchError}
          </p>
        ) : null}

        {searchPerformed && !searchLoading && !searchHasResults && !searchError ? (
          <p className="alert" role="status">
            No results found
          </p>
        ) : null}

        {searchLoading ? (
          <p className="alert" role="status">
            검색 중입니다…
          </p>
        ) : null}

        {searchResults.daily.length ? (
          <SearchSection
            heading="Daily (최근 14일)"
            articles={searchResults.daily}
            visibleCount={visibleSearchDailyCount}
            onLoadMore={() => handleSearchLoadMore('daily')}
            registerRef={registerSearchCardRef}
          />
        ) : null}

        {searchResults.weekly.length ? (
          <SearchSection
            heading="Weekly"
            articles={searchResults.weekly}
            visibleCount={visibleSearchWeeklyCount}
            onLoadMore={() => handleSearchLoadMore('weekly')}
            registerRef={registerSearchCardRef}
            isWeekly
          />
        ) : null}
      </section>
    </main>
  );
}

const TABS = [
  { id: 'daily', label: 'Daily IT/Science' },
  { id: 'weekly', label: 'Weekly SciTech' },
];

function SidebarList({ items, loading, error, selected, onSelect, isCompact, isOpen, onToggle }) {
  if (loading) {
    return (
      <div className="sidebar__collapsible">
        <p className="status-line">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sidebar__collapsible">
        <p className="alert" role="status">
          {error}
        </p>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="sidebar__collapsible">
        <p className="status-line">데이터가 없습니다.</p>
      </div>
    );
  }

  if (isCompact) {
    const selectedItem = items.find((item) => item.value === selected) || items[0];
    return (
      <div className="sidebar__collapsible">
        <button
          type="button"
          className="sidebar__toggle"
          aria-expanded={isOpen ? 'true' : 'false'}
          onClick={onToggle}
        >
          <span className="sidebar__toggle-label">{selectedItem.label}</span>
          {selectedItem?.isNew ? <span className="badge badge--inline">New</span> : null}
        </button>
        <div className="sidebar__panel" hidden={!isOpen}>
          <ul className="sidebar__list sidebar__list--compact">
            {items.map((entry) => (
              <li key={entry.value}>
                <button
                  type="button"
                  className="sidebar__button"
                  aria-pressed={selected === entry.value}
                  onClick={() => {
                    onSelect(entry.value);
                    onToggle();
                  }}
                >
                  <span>{entry.label}</span>
                  {entry.isNew ? <span className="badge">New</span> : null}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  return (
    <ul className="sidebar__list">
      {items.map((entry) => (
        <li key={entry.value}>
          <button
            type="button"
            className="sidebar__button"
            aria-pressed={selected === entry.value}
            onClick={() => onSelect(entry.value)}
          >
            <span>{entry.label}</span>
            {entry.isNew ? <span className="badge">New</span> : null}
          </button>
        </li>
      ))}
    </ul>
  );
}

function SearchSection({
  heading,
  articles,
  visibleCount,
  onLoadMore,
  registerRef,
  isWeekly = false,
}) {
  const visibleItems = articles.slice(0, visibleCount);
  const hasMore = visibleCount < articles.length;

  return (
    <section>
      <h3 className="section-heading">{heading}</h3>
      <div className="card-grid">
        {visibleItems.map((article) => (
          <ArticleCard
            key={`search-${article.id}`}
            article={article}
            isWeekly={isWeekly}
            registerRef={(id) => registerRef(`search-${id}`)}
          />
        ))}
      </div>
      {hasMore ? (
        <button type="button" className="load-more" onClick={onLoadMore}>
          Load More
        </button>
      ) : visibleItems.length ? (
        <div className="status-line" role="status">
          No more results
        </div>
      ) : null}
    </section>
  );
}
