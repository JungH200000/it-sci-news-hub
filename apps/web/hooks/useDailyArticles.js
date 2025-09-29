import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '../lib/api';

const PAGE_SIZE = 10;

export function useDailyArticles(date) {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  // 날짜가 변경되면 useEffect가 즉시 반응
  useEffect(() => {
    if (!date) {
      // date가 없으면
      setItems([]); // 목록을 비우고
      setHasMore(false); // hasMore을 false로 만들고
      return; // 종료
    }

    let cancelled = false;

    // 초기 로드 : 1페이지를 가져옴
    async function loadInitial() {
      setLoading(true);
      setError(null);
      try {
        const result = await apiGet('/articles/daily', {
          date,
          page: 1,
          size: PAGE_SIZE,
        });
        if (cancelled) return;
        const payload = result?.data || {};
        setItems(Array.isArray(payload.items) ? payload.items : []);
        setHasMore(Boolean(payload.hasMore));
        setPage(1);
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load articles');
          setItems([]);
          setHasMore(false);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
          setLoadingMore(false);
        }
      }
    }

    loadInitial();
    return () => {
      cancelled = true;
    };
  }, [date]);

  // '더보기' : 다음 페이지를 이어 붙임
  const loadMore = useCallback(async () => {
    if (!date || loading || loadingMore || !hasMore) {
      return null;
    }
    setLoadingMore(true);
    try {
      const nextPage = page + 1;
      const result = await apiGet('/articles/daily', {
        date,
        page: nextPage,
        size: PAGE_SIZE,
      });
      const payload = result?.data || {};
      const newItems = Array.isArray(payload.items) ? payload.items : [];
      setItems((prev) => [...prev, ...newItems]);
      setPage(nextPage);
      setHasMore(Boolean(payload.hasMore));
      return newItems[0]?.id ?? null;
    } catch (err) {
      setError(err.message || 'Failed to load more articles');
      return null;
    } finally {
      setLoadingMore(false);
    }
  }, [date, hasMore, loading, loadingMore, page]);

  return {
    items,
    hasMore,
    loading,
    loadingMore,
    error,
    loadMore,
  };
}
