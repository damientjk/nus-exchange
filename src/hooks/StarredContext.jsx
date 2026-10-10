import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { legacyMappingKey } from '../lib/mappings.js';
import { loadLegacyIds, useMappings } from './useMappings.js';

const STAR_KEY = 'nus-exchange-starred-mappings';
const StarredContext = createContext(null);

function loadStarred() {
  try {
    const raw = window.localStorage.getItem(STAR_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveStarred(starred) {
  try {
    window.localStorage.setItem(STAR_KEY, JSON.stringify(starred));
  } catch {
    // storage unavailable
  }
}

const isLegacyKey = (key) => key.includes('|||');

export function StarredProvider({ children }) {
  const [starred, setStarred] = useState(loadStarred);
  const { records } = useMappings();

  // Stars saved before mappings had ids are keyed by legacyMappingKey; move
  // them onto ids. Where an old key matched several mappings, all of them
  // showed as starred, so all of them stay starred.
  useEffect(() => {
    if (!records || !Object.keys(starred).some(isLegacyKey)) return;
    let cancelled = false;
    loadLegacyIds()
      .then(({ keys: renamed }) => {
        if (cancelled) return;
        const idsByKey = new Map();
        for (const r of records) {
          const key = legacyMappingKey(r);
          if (!idsByKey.has(key)) idsByKey.set(key, []);
          idsByKey.get(key).push(r.id);
        }
        setStarred((prev) => {
          const next = {};
          for (const key of Object.keys(prev)) {
            if (!isLegacyKey(key)) next[key] = true;
            else for (const id of renamed[key] || idsByKey.get(key) || []) next[id] = true;
          }
          saveStarred(next);
          return next;
        });
      })
      .catch(() => {
        // keep the old keys and try again on the next visit
      });
    return () => {
      cancelled = true;
    };
  }, [records, starred]);

  const toggleStar = useCallback((record) => {
    setStarred((prev) => {
      const next = { ...prev };
      if (next[record.id]) delete next[record.id];
      else next[record.id] = true;
      saveStarred(next);
      return next;
    });
  }, []);

  const starMany = useCallback((records) => {
    setStarred((prev) => {
      const next = { ...prev };
      for (const record of records) next[record.id] = true;
      saveStarred(next);
      return next;
    });
  }, []);

  const isStarred = useCallback((record) => !!starred[record.id], [starred]);

  const starredCount = useMemo(
    () => Object.keys(starred).filter((k) => !isLegacyKey(k)).length,
    [starred],
  );

  const value = useMemo(
    () => ({ starred, isStarred, toggleStar, starMany, starredCount }),
    [starred, isStarred, toggleStar, starMany, starredCount],
  );

  return <StarredContext.Provider value={value}>{children}</StarredContext.Provider>;
}

export function useStarred() {
  const ctx = useContext(StarredContext);
  if (!ctx) throw new Error('useStarred must be used within StarredProvider');
  return ctx;
}
