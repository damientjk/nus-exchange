import { teachingLanguage } from '../lib/language.js';

const linkClass = 'font-semibold text-accent hover:text-accent-hover';

const LANGUAGE_STYLE = {
  yes: 'border-[#cfe5d3] bg-[#eef7f0] text-[#2f6b3a]',
  mostly: 'border-[#cfe5d3] bg-[#eef7f0] text-[#2f6b3a]',
  no: 'border-accent-border bg-accent-bg text-accent-hover',
  unknown: 'border-border-input bg-bg text-muted',
};

export default function OverseasCourseInfo({ code, title, url, lang, partnerUni, country }) {
  const language = teachingLanguage(lang, partnerUni, country);
  const search = `https://www.google.com/search?q=${encodeURIComponent(
    [code && `"${code}"`, title, partnerUni].filter(Boolean).join(' '),
  )}`;

  return (
    <>
      {url ? (
        <a href={url} target="_blank" rel="noopener noreferrer" className={linkClass}>
          Course page at {partnerUni} ↗
        </a>
      ) : (
        <div>
          <span className="text-muted-3">No course page on file. </span>
          <a href={search} target="_blank" rel="noopener noreferrer" className={linkClass}>
            Search the web ↗
          </a>
        </div>
      )}
      <div>
        <span
          className={`inline-block rounded-full border px-2.5 py-0.5 text-[11.5px] font-semibold ${LANGUAGE_STYLE[language.status]}`}
        >
          {language.label}
        </span>
        <div className="mt-1 text-[11.5px] text-muted-3">{language.detail}</div>
      </div>
    </>
  );
}
