import { useEffect, useState } from 'react';
import { apiGet } from '../lib/api';

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];

function formatDateLabel(dateStr) {
  try {
    const date = new Date(`${dateStr}T00:00:00`);
    if (Number.isNaN(date.getTime())) return dateStr;
    const weekday = WEEKDAYS[date.getDay()];
    return `${dateStr} (${weekday})`;
  } catch (error) {
    return dateStr;
  }
}

export function useDailySidebar() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchDates() {
      setLoading(true);
      setError(null);
      try {
        const result = await apiGet('/articles/sidebar/daily');
        if (cancelled) return;
        const data = Array.isArray(result?.data) ? result.data : [];
        const mapped = data.map((value, index) => ({
          value,
          label: formatDateLabel(value),
          isNew: index === 0,
        }));
        setItems(mapped);
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load dates');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchDates();
    return () => {
      cancelled = true;
    };
  }, []);

  return { items, loading, error };
}
