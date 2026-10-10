import { useEffect, useState } from 'react';

const API = 'https://api.nusmods.com/v2';
const found = new Map(); // code -> academic year it was found in, or null

// NUSMods publishes the next academic year around July. Look in the current
// year first, then the two before it for modules that have since been retired.
function recentAcadYears() {
  const now = new Date();
  const start = now.getMonth() >= 6 ? now.getFullYear() : now.getFullYear() - 1;
  return [0, 1, 2].map((back) => `${start - back}-${start - back + 1}`);
}

async function findOnNusMods(code) {
  if (found.has(code)) return found.get(code);
  for (const ay of recentAcadYears()) {
    const res = await fetch(`${API}/${ay}/modules/${encodeURIComponent(code)}.json`);
    if (res.ok) {
      found.set(code, ay);
      return ay;
    }
    if (res.status !== 404) throw new Error(`HTTP ${res.status}`);
  }
  found.set(code, null);
  return null;
}

const linkClass = 'font-semibold text-accent hover:text-accent-hover';

export default function NusModsLink({ code }) {
  // 'checking' | 'found' | 'missing' | 'unreachable'
  const [state, setState] = useState(() =>
    found.has(code) ? (found.get(code) ? 'found' : 'missing') : 'checking',
  );
  const [ay, setAy] = useState(() => found.get(code) || null);

  useEffect(() => {
    let cancelled = false;
    findOnNusMods(code)
      .then((year) => {
        if (cancelled) return;
        setAy(year);
        setState(year ? 'found' : 'missing');
      })
      .catch(() => {
        if (!cancelled) setState('unreachable');
      });
    return () => {
      cancelled = true;
    };
  }, [code]);

  const url = `https://nusmods.com/courses/${encodeURIComponent(code)}`;

  if (state === 'checking') return <span className="text-muted-3">Checking NUSMods…</span>;
  if (state === 'missing') {
    return (
      <span className="text-muted-3">
        Not on NUSMods in the last three years. The code may be retired or renamed.
      </span>
    );
  }
  const current = ay === recentAcadYears()[0];
  return (
    <a href={url} target="_blank" rel="noopener noreferrer" className={linkClass}>
      View on NUSMods ↗
      {state === 'found' && !current && (
        <span className="ml-1 font-normal text-muted-3">(last listed AY{ay.replace('-', '/')})</span>
      )}
    </a>
  );
}
