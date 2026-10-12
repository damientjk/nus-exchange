# exchange.map

website to help students map mods for exchange bc edurec SUCKSSSS

Search real, previously-approved NUS exchange module mappings across partner universities
before you plan your application — 21,000+ mappings across 374 partner universities in 45
countries.

## Features

- **Search** by course code, module title, or university, and narrow by any mix of
  countries, universities and NUS modules (pick several of each), plus faculty and NUS
  module-prefix filters (e.g. `EE`, `ME`, `CS`). All of it lives in the URL, so results are
  shareable/bookmarkable.
- **Browse** partner universities grouped by country.
- **Detail view** for each mapping, correctly showing combined mappings (e.g. two overseas
  modules bundling into one NUS module, or vice versa) rather than implying two separate 1:1
  pairs. Each NUS module links to NUSMods (checked live against the NUSMods API), each overseas
  module links to its official course page where one was found, and shows whether it's taught
  in English.
- **My Mappings** — star mappings to save them, persisted in `localStorage`.
- Infinite scroll on search results (loads 100 at a time).

## Tech stack

React 19 + Vite + React Router + Tailwind CSS v4. No backend — it's a static site that fetches
a pre-built JSON dataset at runtime.

## Getting started

```
pnpm install
pnpm dev       # dev server
pnpm build     # production build -> dist/
pnpm preview   # serve the production build locally
```

## Project structure

```
src/
  pages/       Home, Search, Browse, Saved, Detail — one per route
  components/  Header, ResultCard, ModuleCard, Loading
  hooks/       useMappings (fetches the dataset), StarredContext (starred/saved state)
  lib/         filtering, grouping, and stats helpers over the dataset
data/
  exchange-mappings.xlsx  source workbook (official NUS module-mapping data)
  EduRec Scrape 2026.xlsx mappings scraped from EduRec in Oct 2026, same columns plus faculty
  *.pdf                   departments' lists of previously approved mappings
  extract_pdf_mappings.py turns those PDFs into approved-lists/*.csv
  approved-lists/         the PDFs' mappings as CSV (generated, committed)
  build_data.py           merges all of the above into public/modules-data.json
  check_course_pages.py   finds and verifies overseas course pages -> course-pages.json
  course-pages.json       verified course-page links and teaching languages (generated)
  make_legacy_ids.py      one-off: maps pre-id links and stars to ids
public/
  modules-data.json       generated dataset, fetched by the app at runtime
  legacy-ids.json         old /mappings/<index> links and stars -> ids, fetched only when needed
```

## Updating the data

The dataset comes from `data/exchange-mappings.xlsx`. To regenerate `public/modules-data.json`
after updating that file:

```
pip3 install openpyxl
pnpm build-data
```

Each mapping gets a stable `id`, a hash of its faculty, university and course codes, which is
what detail-page URLs and stars use, so rebuilding the data doesn't break saved links.

Partner university → country is a hand-maintained lookup in `data/build_data.py` (the source
workbook doesn't include country). If a new partner university shows up in the workbook, the
script will still include its mappings but log a `WARNING: missing country mapping for: [...]`
— add it to the `COUNTRY` dict in that file.

### Sources

Mappings come from four sources: the original workbook, the EduRec scrape, and the Psychology
and Faculty of Science approved-mapping PDFs. A mapping in more than one (same university and
course codes, whatever the faculty) becomes a single record whose `sources` lists all of them in
the order of `SOURCE_PRIORITY` in `build_data.py` (Psych, FOS, original, EduRec). The site
labels each mapping with the first, using `src/lib/sources.js`. The record's details (titles,
units) come from the first source read, which is the original workbook, then EduRec, then the
PDFs, so units are kept where any source has them.

### Departments' approved-mapping lists

Some departments publish their own PDF lists of previously approved mappings, which cover
mappings the workbook doesn't (e.g. Psychology, which the workbook has none of). These come in
as CSVs in `data/approved-lists/`, one per PDF, which `build_data.py` merges in:

```
pip3 install pdfplumber certifi
python3 data/extract_pdf_mappings.py   # PDFs -> data/approved-lists/*.csv
pnpm build-data
```

The extract script renames universities to the workbook's spelling (`UNI_NAMES`), fixes text
the PDFs spilled from long titles into the NUS code column, and fills NUS titles the PDFs leave
out from NUSMods.

To add a new PDF: put it in `data/`, add it to `SOURCES` in `extract_pdf_mappings.py` and to
`APPROVED_LISTS` and `SOURCE_PRIORITY` in `build_data.py`, add a label to `src/lib/sources.js`, and
map any unfamiliar university names in `UNI_NAMES` (or add new universities to `COUNTRY`).

### Overseas course pages and teaching language

The workbook has no links to overseas course pages, so `data/check_course_pages.py` builds
them for universities whose catalogue has a predictable per-course URL (KTH, Lund, Linköping,
Monash, Sydney, UQ, ANU, UNSW, UCD, Georgia Tech, UNC, UIUC). It fetches every candidate URL and
keeps only the ones that really are a course page, reading the teaching language off the page
where the catalogue states it. Results are cached in `data/course-pages.json`, so a rerun only
checks codes that are new. To add a university, add an entry to `SITES` in that script.

```
pip3 install openpyxl certifi
python3 data/check_course_pages.py   # add --recheck to check everything again
pnpm build-data
```

Where no course page states the language, the site falls back to the university as a whole
(`src/lib/language.js`): English-medium countries and a short list of English-medium
universities show as taught in English, Hong Kong as usually English, and everywhere else as
"check the course page".
