#!/usr/bin/env python3
"""Turns the departments' "previously approved mappings" PDFs into CSVs that
data/build_data.py merges into the dataset alongside the workbook.
Run: python3 data/extract_pdf_mappings.py   (needs: pip3 install pdfplumber)

Only needs rerunning when a new PDF comes out; the CSVs in data/approved-lists/
are committed, so building the data doesn't need pdfplumber or the network.

Along the way it:
  - renames universities to the spelling the workbook uses, so build_data.py's
    COUNTRY lookup and aliases apply to them unchanged
  - puts back title text the PDF spilled into the NUS code cell when it cut a
    long title short (e.g. "...Molecule" + "sCM4225")
  - fills in NUS course titles the PDF leaves out, from NUSMods
"""
import csv
import json
import re
import ssl
import urllib.request
from datetime import date
from pathlib import Path

import pdfplumber

DATA = Path(__file__).parent
OUT_DIR = DATA / "approved-lists"

# (PDF, output CSV). The CSV's name is one of the record's `sources` in the dataset;
# build_data.py's APPROVED_LISTS says which faculty each one belongs to.
SOURCES = [
    ("Psych Previously Approved 2026.pdf", "psych-2026.csv"),
    ("FOS Previously Approved 2026.pdf", "fos-2026.csv"),
]

# PDF spelling -> the workbook's (raw, pre-clean_uni_name) spelling, or a new
# name for a university the workbook doesn't have (add those to COUNTRY in
# build_data.py).
UNI_NAMES = {
    "Albert-Ludwigs University of Freiburg": "University of Freiburg",
    "Case Western Reserve Uni": "Case Western Reserve University",
    "Catholic Uni the Sacred Heart": "Catholic University of the Sacred Heart",
    "Chalmers Uni of Technology": "Chalmers University of Technology",
    "Cornell University College of Agriculture & Life Sciences": "Cornell Univ Coll of Agriculture & Life Sciences",
    "Cornell University College of Human Ecology": "Cornell Univ Coll of Human Ecology",
    "Ecole Poly Federale Lausanne": "Ecole Polytechnique Federale de Lausanne (EPFL)",
    "Eindhoven Uni of Technology": "Eindhoven University of Technology",
    "Erasmus University Rotterdam": "Erasmus University",
    "Ewha Women's University, Seoul": "Ewha Women's University,Seoul",
    "Georgia Inst of Technology": "Georgia Institute of Technology",
    "Hong Kong Uni of Sci & Tech": "Hong Kong University of Science & Technology",
    "Humboldt University Berlin": "Humboldt University of Berlin",
    "Interdisciplinary Center Herzliya (IDC)": "Reichman University",  # renamed in 2021
    "Jagiellonian University, Poland": "Jagiellonian University",
    "KTH Royal Institute of Technology": "KTH-Royal Institute of Technology",
    "KTH-Royal Inst of Technology": "KTH-Royal Institute of Technology",
    "Karlsruhe Inst of Technology": "Karlsruhe Institute of Technology",
    "Katholieke Universiteit Leuven (KU Leuven)": "KU Leuven",
    "Korea Adv Inst S&T (KAIST)": "Korea Advanced Institute of Science and Technology",
    "La Trobe University": "LaTrobe University",
    "Ludwig Maximilian U of Munich": "Ludwig Maximilian University of Munich",
    "Ludwig-Maximilians-University of Munich": "Ludwig Maximilian University of Munich",
    "MCI - Intl Hochschul GmbH": "MCI - Internationale Hochschule GmbH",
    "Nat'l Yang Ming Chiao Tung Uni": "National Yang Ming Chiao Tung University",
    "Norwegian Uni of Sci & Tech": "Norwegian University of Science and Technology",
    "Norwegian University of Science & Technology": "Norwegian University of Science and Technology",
    "Osaka University": "University of Osaka",
    "Otto Beisheim School of Management": "WHU - Otto Beisheim School of Management",
    "Pennsylvania State University": "Pennsylvania State University, The",
    "Pohang Uni of Sci & Technology": "Pohang University of Science and Technology",
    "RPTU Kaiserslautern-Landau": "University of Kaiserslautern, FRG",  # merged into RPTU in 2023
    "Ritsumeikan University": "Ritsumeikan University,Kyoto",
    "Sciences Po": "Sciences Po Paris",
    "Technical Uni of Darmstadt": "Technical University of Darmstadt",
    "Technical Uni of Denmark": "Technical University of Denmark",
    "Technical Uni of Munich": "Technical University of Munich",
    "The Australian National Uni": "Australian National University, The",
    "The Australian National University": "Australian National University, The",
    "The Chinese Uni of Hong Kong": "Chinese University of Hong Kong, The",
    "The Chinese University of Hong Kong": "Chinese University of Hong Kong, The",
    "The College of William & Mary": "William & Mary",
    "The George Washington Uni": "George Washington University, The",
    "The George Washington University": "George Washington University, The",
    "The Hong Kong Polytechnic Uni": "Hong Kong Polytechnic University, The",
    "The Hong Kong Polytechnic University": "Hong Kong Polytechnic University, The",
    "The Hong Kong University of Science and Technology": "Hong Kong University of Science & Technology",
    "The Pennsylvania State Uni": "Pennsylvania State University, The",
    "The Uni of British Columbia": "University of British Columbia, The",
    "The Uni of Texas at Austin": "University of Texas at Austin, The",
    "The Uni of Western Australia": "University of Western Australia, The",
    "The University of Arizona": "University of Arizona, The",
    "The University of Auckland": "University of Auckland, The",
    "The University of British Columbia": "University of British Columbia, The",
    "The University of British Columbia (Okanagan)": "University of British Columbia (Okanagan), The",
    "The University of Edinburgh": "University of Edinburgh, The",
    "The University of Hong Kong": "University of Hong Kong, The",
    "The University of Manchester": "University of Manchester, The",
    "The University of Melbourne": "University of Melbourne, The",
    "The University of New South Wales": "University of New South Wales",
    "The University of North Carolina at Chapel Hill": "University of North Carolina at Chapel Hill, The",
    "The University of Nottingham": "University of Nottingham",
    "The University of Queensland": "University of Queensland, The",
    "The University of Sheffield": "University of Sheffield, The",
    "The University of Sydney": "University of Sydney, The",
    "The University of Texas at Austin": "University of Texas at Austin, The",
    "The University of Tokyo": "University of Tokyo, The",
    "The University of Virginia": "University of Virginia",
    "The University of Western Australia": "University of Western Australia, The",
    "Tokyo Institute of Technology": "Institute of Science Tokyo",  # merged in 2024
    "UBC (Okanagan)": "University of British Columbia (Okanagan), The",
    "Uni Illinois Urbana-Champaign": "University of Illinois Urbana-Champaign",
    "Uni N Carolina at Chapel Hill": "University of North Carolina at Chapel Hill, The",
    "Uni of Southern California": "University of Southern California",
    "Uni of Tor (Mississauga)": "University of Toronto (Mississauga)",
    "Uni of Tor (Scarborough)": "University of Toronto (Scarborough)",
    "Uni of Wisconsin-Madison": "University of Wisconsin-Madison",
    "University College Cork, Ireland": "University College Cork",
    "University Medical Ctr Utrecht": "University Medical Center Utrecht",
    "University of Concordia": "Concordia University",
    "University of Illinois at Urbana-Champaign": "University of Illinois Urbana-Champaign",
    "University of Michigan, Ann Arbor": "University of Michigan",
    "University of Toronto Mississauga": "University of Toronto (Mississauga)",
    "University of Toronto Scarborough": "University of Toronto (Scarborough)",
    "University of Trento": "Universita degli Studi di Trento",
    "Utrecht University (University Medical Center Utrecht)": "University Medical Center Utrecht",
    "Victoria Uni of Wellington": "Victoria University of Wellington",
}

NUSMODS = "https://api.nusmods.com/v2/{}/moduleList.json"
COURSE_CODE = re.compile(r"[A-Z]{2,4}\d{4}[A-Z]{0,2}")


def nusmods_titles():
    """code -> title over the last few academic years, newest title winning."""
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    today = date.today()
    start = today.year if today.month >= 7 else today.year - 1
    titles = {}
    for y in range(start - 4, start + 1):
        try:
            with urllib.request.urlopen(NUSMODS.format(f"{y}-{y + 1}"), context=ctx, timeout=60) as res:
                for m in json.load(res):
                    titles[m["moduleCode"]] = m["title"]
        except Exception as e:  # a year not published yet, or offline
            print(f"  NUSMods {y}-{y + 1}: {e}")
    return titles


def read_pdf(path):
    """Yields each table row as [uni, pu code, pu title, nus code, nus title]."""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    row = [" ".join((c or "").split()) for c in row]
                    if not row[0] or row[0].startswith(("NUS Department", "Partner University")):
                        continue  # page header
                    yield (row + [""])[:5]


def split_nus_code(cell, titles, known):
    """Splits the NUS code cell into (title spill-over, code). A spilled capital
    looks like part of the code ("AENV4991"), so that's only split off when the
    code isn't on NUSMods but the rest of it is a code we know."""
    m = re.match(r"([^A-Z]*)(.*)", cell)
    spill, code = m.group(1), m.group(2)
    if code not in titles and code[1:] in known:
        spill, code = spill + code[0], code[1:]
    return spill.lstrip(","), code


def main():
    print("fetching NUS course titles from NUSMods")
    titles = nusmods_titles()
    OUT_DIR.mkdir(exist_ok=True)
    for pdf_name, csv_name in SOURCES:
        rows = list(read_pdf(DATA / pdf_name))
        known = set(titles) | {r[3] for r in rows if COURSE_CODE.fullmatch(r[3])}
        out, seen = [], set()
        for uni, pu_code, pu_title, nus_cell, nus_title in rows:
            spill, nus_code = split_nus_code(nus_cell, titles, known)
            if spill:
                pu_title += spill
            nus_title = re.sub(r"^PL-Level (\d)000", r"PL Level-\g<1>000", nus_title)
            rec = (UNI_NAMES.get(uni, uni), pu_code, pu_title, nus_code, nus_title or titles.get(nus_code, ""))
            if rec not in seen:
                seen.add(rec)
                out.append(rec)
        with open(OUT_DIR / csv_name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["partnerUni", "puCourse", "puCourseTitle", "nusCourse", "nusCourseTitle"])
            w.writerows(out)
        untitled = sorted({r[3] for r in out if not r[4]})
        print(f"{pdf_name}: {len(out)} mappings ({len(rows) - len(out)} duplicate rows dropped) -> {csv_name}")
        if untitled:
            print(f"  no NUS title for {len(untitled)} codes: {' '.join(untitled)}")


if __name__ == "__main__":
    main()
