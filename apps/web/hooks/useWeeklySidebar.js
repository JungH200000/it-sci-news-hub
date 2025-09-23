import { useEffect, useState } from 'react';
import { apiGet } from '../lib/api';

function formatWeekLabel(weekKey) {
  if (!weekKey) return '';
  const [year, month, nth] = weekKey.split('-');
  if (!year || !month || !nth) {
    return weekKey;
  }
  return `${parseInt(year, 10)}년 ${parseInt(month, 10)}월 ${nth}주차`;
}

export function useWeeklySidebar() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchWeeks() {
      setLoading(true);
      setError(null);
      try {
        const result = await apiGet('/articles/sidebar/weekly');
        if (cancelled) return;
        const data = Array.isArray(result?.data) ? result.data : [];
        const mapped = data.map((value, index) => ({
          value,
          label: formatWeekLabel(value),
          isNew: index === 0,
        }));
        setItems(mapped);
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load weeks');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchWeeks();
    return () => {
      cancelled = true;
    };
  }, []);

  return { items, loading, error };
}
