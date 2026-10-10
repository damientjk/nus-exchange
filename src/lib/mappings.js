export const FACULTY_SHORT = {
  'College of Design and Engineering': 'CDE',
  'NUS Business School': 'Business',
  'Faculty of Arts & Social Sciences': 'FASS',
  'Faculty of Science': 'Science',
  'School of Computing': 'Computing',
  'Other Programmes': 'Other',
};

export const FACULTY_OPTIONS = ['All', ...Object.keys(FACULTY_SHORT)];

// Stars used to be keyed this way, which let two different mappings share a
// key. Only used now to migrate stars saved before mappings had ids.
export function legacyMappingKey(r) {
  return [r.partnerUni, r.nusCourse1, r.puCourse1, r.faculty].join('|||');
}

export function computeStats(records) {
  const unis = new Set(records.map((r) => r.partnerUni));
  const countries = new Set(records.map((r) => r.country));
  return { mappingCount: records.length, uniCount: unis.size, countryCount: countries.size };
}

export function groupByCountry(records) {
  const byCountry = new Map();
  for (const r of records) {
    if (!byCountry.has(r.country)) {
      byCountry.set(r.country, { country: r.country, unis: new Set(), count: 0 });
    }
    const entry = byCountry.get(r.country);
    entry.unis.add(r.partnerUni);
    entry.count += 1;
  }
  return [...byCountry.values()].sort((a, b) => b.count - a.count);
}

const PREFIX_RE = /^[A-Za-z&]+/;

export function coursePrefix(code) {
  const m = PREFIX_RE.exec(code || '');
  return m ? m[0].toUpperCase() : null;
}

export function groupPrefixes(records) {
  const counts = new Map();
  for (const r of records) {
    const prefix = coursePrefix(r.nusCourse1);
    if (!prefix) continue;
    counts.set(prefix, (counts.get(prefix) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([prefix, count]) => ({ prefix, count }));
}

export function groupUniversitiesByCountry(records) {
  const countries = groupByCountry(records);
  return countries.map((c) => {
    const uniCounts = new Map();
    for (const r of records) {
      if (r.country !== c.country) continue;
      uniCounts.set(r.partnerUni, (uniCounts.get(r.partnerUni) || 0) + 1);
    }
    const universities = [...uniCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count }));
    return { country: c.country, universities };
  });
}

export function parseModuleCodes(text) {
  return [
    ...new Set(
      (text || '')
        .split(/[\n,;]+/)
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean),
    ),
  ];
}

// Ranks partner universities by how many of the given NUS module codes they
// have an approved mapping for. Ties break on the university's total mapping
// count (more approved mappings overall = more flexibility if the plan
// changes), then alphabetically.
export function matchUniversitiesByCodes(records, codes, limit = 5) {
  const codeSet = new Set(codes.map((c) => c.trim().toUpperCase()).filter(Boolean));
  if (codeSet.size === 0) return [];

  const uniMap = new Map();
  for (const r of records) {
    if (!uniMap.has(r.partnerUni)) {
      uniMap.set(r.partnerUni, {
        partnerUni: r.partnerUni,
        country: r.country,
        matched: new Set(),
        matchedRecords: [],
        totalMappings: 0,
      });
    }
    const entry = uniMap.get(r.partnerUni);
    entry.totalMappings += 1;
    let recordMatches = false;
    for (const raw of [r.nusCourse1, r.nusCourse2]) {
      const code = (raw || '').toUpperCase();
      if (code && codeSet.has(code)) {
        entry.matched.add(code);
        recordMatches = true;
      }
    }
    if (recordMatches) entry.matchedRecords.push(r);
  }

  const allCodes = [...codeSet];
  return [...uniMap.values()]
    .filter((u) => u.matched.size > 0)
    .map((u) => ({
      partnerUni: u.partnerUni,
      country: u.country,
      matchCount: u.matched.size,
      totalMappings: u.totalMappings,
      matchedCodes: allCodes.filter((c) => u.matched.has(c)),
      missingCodes: allCodes.filter((c) => !u.matched.has(c)),
      matchedRecords: u.matchedRecords,
    }))
    .sort(
      (a, b) =>
        b.matchCount - a.matchCount ||
        b.totalMappings - a.totalMappings ||
        a.partnerUni.localeCompare(b.partnerUni),
    )
    .slice(0, limit);
}

function nusCodes(r) {
  return r.nusCourse2 ? [r.nusCourse1, r.nusCourse2] : [r.nusCourse1];
}

// Countries and universities combine into one location filter. A university
// whose country is also selected narrows that country to it (Japan + Kyoto
// University = just Kyoto); one whose country isn't selected adds to the
// results (Japan + ETH Zurich = all of Japan and ETH).
function locationMatcher(records, countries, unis) {
  if (!countries.length && !unis.length) return null;
  const countrySet = new Set(countries);
  const uniSet = new Set(unis);
  const narrowed = new Set();
  for (const r of records) {
    if (uniSet.has(r.partnerUni) && countrySet.has(r.country)) narrowed.add(r.country);
  }
  return (r) =>
    uniSet.has(r.partnerUni) || (countrySet.has(r.country) && !narrowed.has(r.country));
}

export function filterRecords(
  all,
  { query, faculty, countries = [], unis = [], modules = [], prefix },
) {
  let recs = all;
  if (faculty && faculty !== 'All') recs = recs.filter((r) => r.faculty === faculty);
  const inLocation = locationMatcher(recs, countries, unis);
  if (inLocation) recs = recs.filter(inLocation);
  if (modules.length) {
    const moduleSet = new Set(modules);
    recs = recs.filter((r) => nusCodes(r).some((c) => moduleSet.has(c)));
  }
  if (prefix) recs = recs.filter((r) => coursePrefix(r.nusCourse1) === prefix);
  const q = (query || '').trim().toLowerCase();
  if (q) {
    recs = recs.filter(
      (r) =>
        (r.nusCourse1 || '').toLowerCase().includes(q) ||
        (r.nusCourse1Title || '').toLowerCase().includes(q) ||
        (r.nusCourse2 || '').toLowerCase().includes(q) ||
        (r.nusCourse2Title || '').toLowerCase().includes(q) ||
        (r.puCourse1 || '').toLowerCase().includes(q) ||
        (r.puCourse1Title || '').toLowerCase().includes(q) ||
        (r.puCourse2 || '').toLowerCase().includes(q) ||
        (r.puCourse2Title || '').toLowerCase().includes(q) ||
        (r.partnerUni || '').toLowerCase().includes(q),
    );
  }
  return recs;
}

// Options for the country / university / module pickers on the search page,
// most mappings first.
export function countryOptions(records) {
  return groupByCountry(records).map((c) => ({
    value: c.country,
    label: c.country,
    count: c.count,
  }));
}

export function universityOptions(records) {
  const unis = new Map();
  for (const r of records) {
    if (!unis.has(r.partnerUni)) {
      unis.set(r.partnerUni, { value: r.partnerUni, label: r.partnerUni, hint: r.country, count: 0 });
    }
    unis.get(r.partnerUni).count += 1;
  }
  return [...unis.values()].sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

export function moduleOptions(records) {
  const mods = new Map();
  for (const r of records) {
    for (const [code, title] of [
      [r.nusCourse1, r.nusCourse1Title],
      [r.nusCourse2, r.nusCourse2Title],
    ]) {
      if (!code) continue;
      if (!mods.has(code)) mods.set(code, { value: code, label: code, hint: title, count: 0 });
      const m = mods.get(code);
      m.count += 1;
      if (!m.hint && title) m.hint = title;
    }
  }
  return [...mods.values()].sort((a, b) => b.count - a.count || a.value.localeCompare(b.value));
}
