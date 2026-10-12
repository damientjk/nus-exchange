// Where each mapping comes from. A record's `sources` lists every source that
// has it, highest priority first (SOURCE_PRIORITY in data/build_data.py), and
// the site labels it with the first.
export const SOURCES = {
  'psych-2026': {
    label: 'Psych 2026',
    full: "the Department of Psychology's list of previous course mappings (Jun 2026)",
  },
  'fos-2026': {
    label: 'FOS 2026',
    full: "the Faculty of Science's list of previously approved mappings (Sep 2026)",
  },
  original: {
    label: 'Original list',
    full: 'the original NUS module-mapping list',
  },
  'edurec-2026-10': {
    label: 'EduRec scrape Oct 2026',
    full: 'the EduRec scrape (Oct 2026)',
  },
};

export function sourceLabel(record) {
  return SOURCES[record.sources?.[0]]?.label || null;
}
