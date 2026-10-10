#!/usr/bin/env python3
"""Finds the official course page for overseas modules, and the teaching
language where the page states it, writing data/course-pages.json.

Only universities whose course catalogue has a predictable per-course URL are
covered (see SITES). Every candidate URL is fetched and checked, so a link
only appears on the site when the page really exists — many catalogues answer
200 with a "not found" page, which is what each site's `exists` check is for.

Run: python3 data/check_course_pages.py            # check codes not yet checked
     python3 data/check_course_pages.py --recheck  # check everything again
then: pnpm build-data

Results, misses included (as null), are cached in data/course-pages.json so a
rerun only fetches codes that are new to the workbook.
"""
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import build_data as b  # noqa: E402

try:
    import certifi  # python.org builds on macOS ship without a CA bundle
    SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL = ssl.create_default_context()

OUT = b.COURSE_PAGES
UA = "Mozilla/5.0 (compatible; exchange.map course-page checker)"
DELAY = 0.5  # seconds between requests to the same site
LANGS = r"(Swedish/English|English/Swedish|English|Swedish)"


def text_of(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def title_of(html):
    m = re.search(r"<title>([^<]*)", html)
    return m.group(1).strip() if m else ""


def split_code(code):
    """CS4641 -> ('CS', '4641'), for catalogues that want 'CS 4641'."""
    m = re.fullmatch(r"([A-Z]+)[\s-]*(\d\w*)", code)
    return m.groups() if m else None


def courseleaf(base):
    """CourseLeaf catalogues: the search page lists a courseblock for a real course."""
    def url(code):
        parts = split_code(code)
        return f"{base}/search/?P={urllib.parse.quote(' '.join(parts))}" if parts else None
    return {"url": url, "exists": lambda html, final: 'class="courseblock' in html}


def kth_lang(html):
    m = re.search(r"Language of instruction " + LANGS, text_of(html))
    return m.group(1) if m else None


def lth_lang(html):
    m = re.search(r"Language of instruction: The course will be given in " + LANGS, text_of(html))
    return m.group(1) if m else None


def liu_lang(html):
    # the course's study-programme table has a language column per programme
    found = set(re.findall(r"\b(Swedish/English|English|Swedish) (?:Link|Norrk)", text_of(html)))
    if not found:
        return None
    return found.pop() if len(found) == 1 else "Swedish/English"


# partnerUni (as cleaned by build_data) -> how to find and verify a course page
SITES = {
    "KTH-Royal Institute of Technology": {
        "url": lambda c: f"https://www.kth.se/student/kurser/kurs/{c}?l=en",
        "exists": lambda html, final: "undefined undefined" not in html,
        "lang": kth_lang,
    },
    "Linkoping University": {
        "url": lambda c: f"https://studieinfo.liu.se/en/kurs/{c}",
        "exists": lambda html, final: True,  # missing courses are a real 404
        "lang": liu_lang,
    },
    "Lund University": {  # LTH (engineering) courses only; others 404
        "url": lambda c: f"https://kurser.lth.se/kursplaner/senaste_eng/{c}.html",
        "exists": lambda html, final: True,
        "lang": lth_lang,
    },
    "Monash University": {
        "url": lambda c: f"https://handbook.monash.edu/current/units/{c}",
        "exists": lambda html, final: True,
    },
    "The University of Sydney": {
        "url": lambda c: f"https://www.sydney.edu.au/units/{c}",
        "exists": lambda html, final: "/errors/" not in final,
    },
    "The University of Queensland": {
        "url": lambda c: f"https://programs-courses.uq.edu.au/course.html?course_code={c}",
        "exists": lambda html, final: not title_of(html).startswith("my.UQ"),
    },
    "The Australian National University": {
        "url": lambda c: f"https://programsandcourses.anu.edu.au/course/{c}",
        "exists": lambda html, final: "/Error/" not in final,
    },
    "University of New South Wales": {
        "url": lambda c: f"https://www.handbook.unsw.edu.au/undergraduate/courses/2026/{c}",
        "fallback": lambda c: f"https://www.handbook.unsw.edu.au/postgraduate/courses/2026/{c}",
        "exists": lambda html, final: True,
    },
    "University College Dublin": {
        "url": lambda c: f"https://hub.ucd.ie/usis/!W_HU_MENU.P_PUBLISH?p_tag=MODULE&MODULE={c}",
        "exists": lambda html, final: "Modules Search" not in title_of(html),
    },
    "Georgia Institute of Technology": courseleaf("https://catalog.gatech.edu"),
    "The University of North Carolina at Chapel Hill": courseleaf("https://catalog.unc.edu"),
    "University of Illinois Urbana-Champaign": courseleaf("https://catalog.illinois.edu"),
}


def fetch(url):
    """Returns (html, final url), or None for a 4xx/5xx or network error."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL) as res:
            return res.read().decode("utf-8", errors="replace"), res.geturl()
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return None


def check(site, code):
    compact = re.sub(r"\s+", "", code)  # the workbook sometimes has "SF 1861" for SF1861
    for make_url in (site["url"], site.get("fallback")):
        url = make_url(compact) if make_url else None
        if not url:
            continue
        got = fetch(url)
        time.sleep(DELAY)
        if got and site["exists"](*got):
            lang = site["lang"](got[0]) if "lang" in site else None
            return {"url": url, **({"lang": lang} if lang else {})}
    return None


def check_site(uni, codes, cache):
    site = SITES[uni]
    found = 0
    for code in codes:
        try:
            result = check(site, code)
        except Exception as e:  # a parsing bug shouldn't lose the other sites' results
            print(f"{uni} {code}: {e!r}", flush=True)
            continue
        cache[f"{uni}|{code}"] = result
        found += result is not None
    print(f"{uni}: {found}/{len(codes)} pages found", flush=True)


def main():
    recheck = "--recheck" in sys.argv
    cache = {} if recheck or not OUT.exists() else json.loads(OUT.read_text(encoding="utf-8"))

    wb = openpyxl.load_workbook(b.SRC, data_only=True)
    todo = {uni: set() for uni in SITES}
    for faculty, partner_raw, row in b.read_rows(wb):
        r = b.build_record(faculty, partner_raw, row)
        if r["partnerUni"] not in SITES:
            continue
        for code in (r["puCourse1"], r["puCourse2"]):
            if code and f"{r['partnerUni']}|{code}" not in cache:
                todo[r["partnerUni"]].add(code)

    # one thread per site: sites are checked in parallel, each one politely
    with ThreadPoolExecutor(max_workers=len(SITES)) as pool:
        for uni, codes in todo.items():
            if codes:
                pool.submit(check_site, uni, sorted(codes), cache)

    OUT.write_text(json.dumps(dict(sorted(cache.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {sum(v is not None for v in cache.values())} pages ({len(cache)} codes checked) to {OUT}")


if __name__ == "__main__":
    main()
