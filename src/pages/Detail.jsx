import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { loadLegacyIds, useMappings } from '../hooks/useMappings.js';
import { useStarred } from '../hooks/StarredContext.jsx';
import ModuleCard from '../components/ModuleCard.jsx';
import NusModsLink from '../components/NusModsLink.jsx';
import OverseasCourseInfo from '../components/OverseasCourseInfo.jsx';
import Loading from '../components/Loading.jsx';
import { SOURCES } from '../lib/sources.js';

// Before mappings had ids, detail URLs used the record's array position.
const LEGACY_IDX = /^\d{1,5}$/;

export default function Detail() {
  const { id } = useParams();
  const { records, error } = useMappings();
  const { isStarred, toggleStar } = useStarred();
  const navigate = useNavigate();

  const rec = useMemo(() => (records ? records.find((r) => r.id === id) : null), [records, id]);
  const relatedAll = useMemo(
    () =>
      records && rec
        ? records.filter((r) => r.partnerUni === rec.partnerUni && r.id !== rec.id)
        : [],
    [records, rec],
  );
  const related = relatedAll.slice(0, 6);

  const isLegacyLink = !!records && !rec && LEGACY_IDX.test(id);
  const [legacyFailed, setLegacyFailed] = useState(false);
  useEffect(() => {
    if (!isLegacyLink) return;
    let cancelled = false;
    loadLegacyIds()
      .then(({ idx }) => {
        if (cancelled) return;
        const newId = idx[Number(id)];
        if (newId) navigate(`/mappings/${newId}`, { replace: true });
        else setLegacyFailed(true);
      })
      .catch(() => {
        if (!cancelled) setLegacyFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [isLegacyLink, id, navigate]);

  if (!records || (isLegacyLink && !legacyFailed)) return <Loading error={error} />;

  if (!rec) {
    return (
      <div className="mx-auto w-full max-w-[760px] px-6 pb-16 pt-10">
        <div className="px-5 py-[60px] text-center text-sm text-muted-3">
          Mapping not found.{' '}
          <button
            type="button"
            onClick={() => navigate('/search')}
            className="font-semibold text-accent hover:text-accent-hover"
          >
            Back to search
          </button>
        </div>
      </div>
    );
  }

  const starred = isStarred(rec);

  const nusCourses = ['1', '2']
    .filter((n) => rec[`nusCourse${n}`])
    .map((n) => ({
      code: rec[`nusCourse${n}`],
      title: rec[`nusCourse${n}Title`],
      units: rec[`nusCrse${n}Units`],
      extra: <NusModsLink code={rec[`nusCourse${n}`]} />,
    }));
  // a couple of overseas modules have a title but no code in the source data
  const puCourses = ['1', '2']
    .filter((n) => rec[`puCourse${n}`] || rec[`puCourse${n}Title`])
    .map((n) => ({
      code: rec[`puCourse${n}`],
      title: rec[`puCourse${n}Title`],
      units: rec[`puCrse${n}Units`],
      extra: (
        <OverseasCourseInfo
          code={rec[`puCourse${n}`]}
          title={rec[`puCourse${n}Title`]}
          url={rec[`puCourse${n}Url`]}
          lang={rec[`puCourse${n}Lang`]}
          partnerUni={rec.partnerUni}
          country={rec.country}
        />
      ),
    }));

  return (
    <div className="mx-auto w-full max-w-[760px] px-6 pb-16 pt-10 max-sm:px-4">
      <div className="mb-[22px] flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-[13px] font-semibold text-muted-2 hover:text-ink"
        >
          ← Back to results
        </button>
        <button
          type="button"
          onClick={() => toggleStar(rec)}
          className="flex items-center gap-1.5 text-[13px] font-semibold"
          style={{ color: starred ? 'var(--color-accent)' : 'var(--color-muted-3)' }}
        >
          <span className="text-lg">{starred ? '★' : '☆'}</span>
          {starred ? 'Saved to My Mappings' : 'Save to My Mappings'}
        </button>
      </div>

      <div className="mb-[18px] flex flex-wrap items-center gap-2.5">
        <div className="rounded-full bg-accent-bg px-[11px] py-[5px] text-xs font-bold text-accent-hover">
          {rec.faculty}
        </div>
        <div className="text-[13px] text-muted">
          {rec.partnerUni} · {rec.country}
        </div>
      </div>

      {(puCourses.length > 1 || nusCourses.length > 1) && (
        <div className="mb-3.5 text-[12.5px] text-muted-2">
          {puCourses.length > 1
            ? `These ${puCourses.length} overseas modules together map to this NUS module.`
            : `This overseas module maps to these ${nusCourses.length} NUS modules.`}
        </div>
      )}

      <div className="flex items-stretch gap-5 max-sm:flex-col">
        <ModuleCard label="NUS module" courses={nusCourses} />
        <div className="flex flex-none items-center justify-center self-center text-xl text-border-input max-sm:rotate-90">
          ⇄
        </div>
        <ModuleCard label="Overseas module" courses={puCourses} />
      </div>

      <div className="mt-3.5 text-[12.5px] leading-snug text-muted-2">
        {rec.sources?.length > 0 && (
          <>
            Source: {rec.sources.map((s) => SOURCES[s]?.full || s).join('; also in ')}.{' '}
          </>
        )}
        {!rec.nusCrse1Units &&
          "This source doesn't list units, so check how many transfer with your faculty."}
      </div>

      <div className="mt-10">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <div className="text-sm font-bold">Other approved mappings at {rec.partnerUni}</div>
          {relatedAll.length > 0 && (
            <button
              type="button"
              onClick={() => navigate(`/search?uni=${encodeURIComponent(rec.partnerUni)}`)}
              className="flex-none text-[13px] font-semibold text-accent hover:text-accent-hover"
            >
              See all {relatedAll.length + 1} mappings →
            </button>
          )}
        </div>
        <div className="flex flex-col gap-2">
          {related.length ? (
            related.map((rel) => (
              <Link
                key={rel.id}
                to={`/mappings/${rel.id}`}
                className="flex items-center justify-between gap-3 rounded-[10px] border border-border bg-white px-4 py-3 hover:border-border-input"
              >
                <div className="text-[13px] font-semibold">
                  {rel.nusCourse1} · {rel.nusCourse1Title}
                </div>
                <div className="flex-none text-xs text-muted-3">{rel.puCourse1}</div>
              </Link>
            ))
          ) : (
            <div className="py-2 text-center text-[12.5px] text-muted-3">
              No other mappings on file for this university yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
