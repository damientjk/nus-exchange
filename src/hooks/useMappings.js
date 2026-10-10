import { useEffect, useState } from 'react';

let cache = null;
let legacyIds = null;

export function useMappings() {
  const [records, setRecords] = useState(cache);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (cache) return;
    let cancelled = false;
    fetch('/modules-data.json')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        cache = data;
        setRecords(cache);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { records, loading: !records && !error, error };
}

// Maps links and stars from before mappings had stable ids (see
// data/make_legacy_ids.py). Only fetched when an old link or star turns up.
export function loadLegacyIds() {
  if (!legacyIds) {
    legacyIds = fetch('/legacy-ids.json').then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    });
    legacyIds.catch(() => {
      legacyIds = null; // let a later call retry
    });
  }
  return legacyIds;
}
