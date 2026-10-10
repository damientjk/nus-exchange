import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMappings } from '../hooks/useMappings.js';
import {
  FACULTY_OPTIONS,
  FACULTY_SHORT,
  countryOptions,
  filterRecords,
  groupPrefixes,
  moduleOptions,
  universityOptions,
} from '../lib/mappings.js';
import ResultCard from '../components/ResultCard.jsx';
import FilterCombobox from '../components/FilterCombobox.jsx';
import Loading from '../components/Loading.jsx';

const PAGE_SIZE = 100;
const PREFIX_COLLAPSE_COUNT = 8;

export default function Search() {
  const { records, error } = useMappings();
  const [params, setParams] = useSearchParams();

  const query = params.get('q') || '';
  const faculty = params.get('faculty') || 'All';
  const prefix = params.get('prefix') || '';
  // Each can be given more than once: ?country=Japan&country=South+Korea
  const countriesParam = params.getAll('country').join('\n');
  const unisParam = params.getAll('uni').join('\n');
  const modulesParam = params.getAll('module').join('\n');
  const countries = useMemo(() => (countriesParam ? countriesParam.split('\n') : []), [countriesParam]);
  const unis = useMemo(() => (unisParam ? unisParam.split('\n') : []), [unisParam]);
  const modules = useMemo(() => (modulesParam ? modulesParam.split('\n') : []), [modulesParam]);

  const inFaculty = useMemo(
    () => (records ? filterRecords(records, { faculty }) : []),
    [records, faculty],
  );
  const facultyScoped = useMemo(
    () => filterRecords(inFaculty, { countries, unis, modules }),
    [inFaculty, countries, unis, modules],
  );
  const prefixOptions = useMemo(() => groupPrefixes(facultyScoped), [facultyScoped]);

  const countryChoices = useMemo(() => countryOptions(inFaculty), [inFaculty]);
  const moduleChoices = useMemo(() => moduleOptions(inFaculty), [inFaculty]);
  const allUniChoices = useMemo(() => universityOptions(inFaculty), [inFaculty]);
  // universities in the chosen countries first
  const uniChoices = useMemo(() => {
    if (!countries.length) return allUniChoices;
    const chosen = new Set(countries);
    return [
      ...allUniChoices.filter((u) => chosen.has(u.hint)),
      ...allUniChoices.filter((u) => !chosen.has(u.hint)),
    ];
  }, [allUniChoices, countries]);

  const [showAllPrefixes, setShowAllPrefixes] = useState(false);
  useEffect(() => setShowAllPrefixes(false), [faculty]);
  const visiblePrefixes = showAllPrefixes
    ? prefixOptions
    : prefixOptions.slice(0, PREFIX_COLLAPSE_COUNT);

  const filtered = useMemo(
    () => filterRecords(facultyScoped, { query, prefix }),
    [facultyScoped, query, prefix],
  );

  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  useEffect(() => setVisibleCount(PAGE_SIZE), [query, faculty, countries, unis, modules, prefix]);
  const results = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  const sentinelRef = useRef(null);
  useEffect(() => {
    if (!hasMore) return;
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((v) => v + PAGE_SIZE);
        }
      },
      { rootMargin: '400px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasMore]);

  function updateParam(key, value) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  }

  function setList(key, values) {
    const next = new URLSearchParams(params);
    next.delete(key);
    for (const v of values) next.append(key, v);
    if (key === 'module') next.delete('prefix');
    setParams(next, { replace: true });
  }

  function clearFilters() {
    const next = new URLSearchParams();
    if (query) next.set('q', query);
    setParams(next, { replace: true });
  }

  function setFaculty(f) {
    const next = new URLSearchParams(params);
    if (f === 'All') next.delete('faculty');
    else next.set('faculty', f);
    next.delete('prefix');
    setParams(next, { replace: true });
  }

  function togglePrefix(p) {
    updateParam('prefix', prefix === p ? '' : p);
  }

  if (!records) return <Loading error={error} />;

  const hasFilters =
    faculty !== 'All' || prefix || countries.length > 0 || unis.length > 0 || modules.length > 0;

  return (
    <div className="mx-auto w-full max-w-[920px] px-6 pb-16 pt-10 max-sm:px-4">
      <div className="mb-[18px] flex gap-2.5">
        <input
          type="text"
          value={query}
          onChange={(e) => updateParam('q', e.target.value)}
          placeholder="Search any course code, module title, or university"
          className="min-w-0 flex-1 rounded-[10px] border border-border-input bg-white px-4 py-[13px] text-sm text-ink outline-none focus:border-accent"
        />
      </div>

      <div className="mb-4 grid grid-cols-3 gap-3 max-md:grid-cols-1">
        <FilterCombobox
          label="Country"
          placeholder="Any country"
          options={countryChoices}
          selected={countries}
          onChange={(v) => setList('country', v)}
        />
        <FilterCombobox
          label="University"
          placeholder="Any university"
          options={uniChoices}
          selected={unis}
          onChange={(v) => setList('uni', v)}
        />
        <FilterCombobox
          label="NUS module"
          placeholder="Any module, e.g. CS2103"
          options={moduleChoices}
          selected={modules}
          onChange={(v) => setList('module', v)}
        />
      </div>

      <div className="mb-2 flex flex-wrap items-center gap-2.5">
        <div className="mr-1 text-xs text-muted-2">Faculty:</div>
        {FACULTY_OPTIONS.map((f) => {
          const active = faculty === f;
          return (
            <button
              key={f}
              type="button"
              onClick={() => setFaculty(f)}
              className={`rounded-full border px-[13px] py-1.5 text-[12.5px] font-semibold ${
                active
                  ? 'border-ink bg-ink text-white'
                  : 'border-border bg-white text-muted'
              }`}
            >
              {f === 'All' ? 'All' : FACULTY_SHORT[f]}
            </button>
          );
        })}

        {hasFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="ml-auto text-[12.5px] font-semibold text-accent hover:text-accent-hover"
          >
            Clear filters
          </button>
        )}
      </div>

      {faculty !== 'All' && prefixOptions.length > 0 && (
        <div className="mb-3 rounded-xl border border-border bg-white/60 px-4 py-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-[11px] font-bold uppercase tracking-wide text-muted-2">
              Filter by module prefix
            </div>
            {prefix && (
              <button
                type="button"
                onClick={() => togglePrefix(prefix)}
                className="text-[11.5px] font-semibold text-accent hover:text-accent-hover"
              >
                Clear
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {visiblePrefixes.map(({ prefix: p, count }) => {
              const active = prefix === p;
              return (
                <button
                  key={p}
                  type="button"
                  onClick={() => togglePrefix(p)}
                  className={`flex items-center gap-1 rounded-full border px-3 py-1.5 text-[12px] font-semibold ${
                    active
                      ? 'border-accent-border bg-accent-bg text-accent-hover'
                      : 'border-border bg-white text-muted hover:border-border-input'
                  }`}
                >
                  {p}
                  <span className={active ? 'text-accent-hover/70' : 'text-muted-3'}>{count}</span>
                </button>
              );
            })}
            {prefixOptions.length > PREFIX_COLLAPSE_COUNT && (
              <button
                type="button"
                onClick={() => setShowAllPrefixes((v) => !v)}
                className="rounded-full border border-dashed border-border-input px-3 py-1.5 text-[12px] font-semibold text-muted-2 hover:text-ink"
              >
                {showAllPrefixes ? 'Show less' : `+${prefixOptions.length - PREFIX_COLLAPSE_COUNT} more`}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="my-2.5 text-[12.5px] text-muted-3">
        {filtered.length} mapping{filtered.length === 1 ? '' : 's'} found
      </div>

      <div className="flex flex-col gap-2.5">
        {results.length ? (
          results.map((r) => <ResultCard key={r.id} record={r} />)
        ) : (
          <div className="px-5 py-[60px] text-center text-sm text-muted-3">
            No mappings found. Try a different course code or clear your filters.
          </div>
        )}
      </div>

      {hasMore && (
        <div ref={sentinelRef} className="py-6 text-center text-[12.5px] text-muted-3">
          Loading more mappings…
        </div>
      )}
    </div>
  );
}
