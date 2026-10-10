// Whether an overseas module is taught in English.
//
// The best source is the course's own page: data/check_course_pages.py reads
// the teaching language off it where the catalogue states one (KTH, Lund,
// Linköping), as puCourse1Lang / puCourse2Lang. Otherwise this falls back to
// what's true of the university as a whole, and says so.

const ENGLISH_COUNTRIES = new Set([
  'Australia',
  'Canada',
  'India',
  'Ireland',
  'New Zealand',
  'Philippines',
  'Singapore',
  'United Kingdom',
  'United States',
]);

// Universities that teach in English despite their country, or the reverse.
const UNIVERSITY_LANGUAGE = {
  'Amsterdam University College': { status: 'yes', note: 'teaches all its courses in English' },
  'Bilkent University': { status: 'yes', note: 'teaches in English' },
  'Bogazici University, Turkey': { status: 'yes', note: 'teaches in English' },
  'Koc University': { status: 'yes', note: 'teaches in English' },
  'Sabanci University': { status: 'yes', note: 'teaches in English' },
  'University College Utrecht': { status: 'yes', note: 'teaches all its courses in English' },
  'HEC Montreal': {
    status: 'unknown',
    note: 'teaches mainly in French, with some courses in English',
  },
  'University of Ottawa': {
    status: 'unknown',
    note: 'teaches many courses in both English and French, as separate sections',
  },
};

const COURSE_LANGUAGE = {
  English: { status: 'yes', label: 'Taught in English' },
  Swedish: { status: 'no', label: 'Taught in Swedish' },
  'Swedish/English': {
    status: 'unknown',
    label: 'Swedish or English',
    detail: 'The course page says it is taught in English if students who don’t speak Swedish enrol.',
  },
  'English/Swedish': {
    status: 'unknown',
    label: 'English or Swedish',
    detail: 'The course page lists both English and Swedish.',
  },
};

// Returns { status: 'yes' | 'mostly' | 'no' | 'unknown', label, detail }.
export function teachingLanguage(courseLang, partnerUni, country) {
  if (courseLang && COURSE_LANGUAGE[courseLang]) {
    const c = COURSE_LANGUAGE[courseLang];
    return { ...c, detail: c.detail || `From ${partnerUni}'s course page.` };
  }

  const uni = UNIVERSITY_LANGUAGE[partnerUni];
  if (uni) {
    return {
      status: uni.status,
      label: uni.status === 'yes' ? 'Taught in English' : 'Check the course page',
      detail: `${partnerUni} ${uni.note}.`,
    };
  }
  if (ENGLISH_COUNTRIES.has(country)) {
    return {
      status: 'yes',
      label: 'Taught in English',
      detail: `${partnerUni} teaches in English.`,
    };
  }
  if (country === 'Hong Kong') {
    return {
      status: 'mostly',
      label: 'Usually in English',
      detail: `English is the main teaching language at ${partnerUni}, but some courses are taught in Cantonese or Mandarin.`,
    };
  }
  return {
    status: 'unknown',
    label: 'Check the course page',
    detail: `Universities in ${country} teach some courses in English and some in the local language, and this one isn't confirmed.`,
  };
}
