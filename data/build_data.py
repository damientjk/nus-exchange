#!/usr/bin/env python3
"""Parses data/exchange-mappings.xlsx into public/modules-data.json for the site.
Run: python3 data/build_data.py

Verified overseas course-page links and teaching languages come from
data/course-pages.json, which data/check_course_pages.py maintains.
"""
import hashlib
import json
import openpyxl
from pathlib import Path

SRC = Path(__file__).parent / "exchange-mappings.xlsx"
OUT = Path(__file__).parent.parent / "public" / "modules-data.json"
COURSE_PAGES = Path(__file__).parent / "course-pages.json"

FACULTY_NAMES = {
    "CDE": "College of Design and Engineering",
    "BIZ": "NUS Business School",
    "FASS": "Faculty of Arts & Social Sciences",
    "FOS": "Faculty of Science",
    "SOC": "School of Computing",
    "MISC": "Other Programmes",
}

# The workbook spells some universities two ways; fold them into one name so
# their mappings aren't split across two entries.
UNI_ALIASES = {
    "Aachen University of Technology": "RWTH Aachen University",
    "Swiss Federal Institute of Technology Lausanne": "Ecole Polytechnique Federale de Lausanne (EPFL)",
    "University of Goteborg": "University of Gothenburg",
}

# Text the workbook already lost to a bad encoding round-trip.
MOJIBAKE = {
    "Europ\ufffd\ufffdenne": "Europ\u00e9enne",
    "\ufffd\ufffd\ufffd": "\u2019",
}

# partnerUni (raw, as it appears in the source workbook) -> country
COUNTRY = {
"Aachen University of Technology": "Germany",
"Aalto University": "Finland",
"Aalto University, Helsinki": "Finland",
"Aalto University, Mikkeli": "Finland",
"Aarhus School of Business": "Denmark",
"Aarhus University": "Denmark",
"Amsterdam University College": "Netherlands",
"Arizona State University": "United States",
"Athens University of Economics & Business": "Greece",
"Australian National University, The": "Australia",
"BI Norwegian Business School": "Norway",
"Beihang University": "China",
"Bilkent University": "Turkey",
"Bogazici University, Turkey": "Turkey",
"Boston College": "United States",
"Boston University": "United States",
"Brandeis University": "United States",
"Bremen University of Applied Sciences": "Germany",
"Budapest University of Technology and Economics": "Hungary",
"Carnegie Mellon University": "United States",
"Case Western Reserve University": "United States",
"Catholic University of Portugal": "Portugal",
"Catholic University of the Sacred Heart": "Italy",
"CentraleSupelec": "France",
"Chalmers University of Technology": "Sweden",
"Chang Gung University": "Taiwan",
"Charles University in Prague": "Czech Republic",
"Chinese University of Hong Kong, The": "Hong Kong",
"Chongqing University": "China",
"Chulalongkorn University": "Thailand",
"City St George's, University of London": "United Kingdom",
"City University of Hong Kong": "Hong Kong",
"Clarkson University": "United States",
"Colgate University": "United States",
"Columbia University": "United States",
"Concordia University": "Canada",
"Copenhagen Business School": "Denmark",
"Cornell Univ Coll of Agriculture & Life Sciences": "United States",
"Cornell Univ Coll of Human Ecology": "United States",
"Cornell University": "United States",
"Corvinus University of Budapest": "Hungary",
"Cracow University of Technology": "Poland",
"Czech Technical University": "Czech Republic",
"Dalhousie University": "Canada",
"Delft University of Technology": "Netherlands",
"Dresden University of Technology": "Germany",
"Duke University": "United States",
"Durham University": "United Kingdom",
"ESSEC Business School": "France",
"ETH Zurich": "Switzerland",
"Eckerd College": "United States",
"Ecole Centrale Des Arts Et Manufactures, Paris": "France",
"Ecole Polytechnique Federale de Lausanne (EPFL)": "Switzerland",
"Ecole Speciale D'Architecture, Paris": "France",
"Eindhoven University of Technology": "Netherlands",
"Emory University": "United States",
"Erasmus University": "Netherlands",
"Esc. Sup. De Admin. Y Dir. De Empresas": "Spain",
"European Business School": "Germany",
"Ewha Women's University,Seoul": "South Korea",
"Franklin W. Olin College of Engineering": "United States",
"Free University of Berlin": "Germany",
"Fudan University": "China",
"George Washington University, The": "United States",
"Georgetown University": "United States",
"Georgetown University Law Center": "United States",
"Georgia Institute of Technology": "United States",
"Grenoble Institute of Technology (Grenoble INP)": "France",
"HEC Montreal": "Canada",
"Hamburg University of Technology": "Germany",
"Hankuk University of Foreign Studies": "South Korea",
"Hanyang University": "South Korea",
"Hautes Etudes Commerciales (HEC) Paris": "France",
"Hebrew University of Jerusalem, The": "Israel",
"Heidelberg University": "Germany",
"Helmut Schmidt University": "Germany",
"Hokkaido University": "Japan",
"Hong Kong Polytechnic University, The": "Hong Kong",
"Hong Kong University of Science & Technology": "Hong Kong",
"Humboldt University of Berlin": "Germany",
"IE Business School": "Spain",
"INSA Lyon": "France",
"Imperial College London": "United Kingdom",
"Indiana University, Bloomington": "United States",
"Institut d'Etudes Politiques de Grenoble": "France",
"Institute of Science Tokyo": "Japan",
"Iowa State University": "United States",
"Istanbul Aydin University": "Turkey",
"Jagiellonian University": "Poland",
"Johns Hopkins University": "United States",
"Justus Liebig University, Giessen": "Germany",
"KTH-Royal Institute of Technology": "Sweden",
"KU Leuven": "Belgium",
"Karlsruhe Institute of Technology": "Germany",
"Karolinska Institute": "Sweden",
"Keio University": "Japan",
"King's College London": "United Kingdom",
"Koc University": "Turkey",
"Korea Advanced Institute of Science and Technology": "South Korea",
"Korea University": "South Korea",
"Kyoto Institute of Technology": "Japan",
"Kyoto University": "Japan",
"Kyushu University": "Japan",
"LaTrobe University": "Australia",
"Leiden University": "Netherlands",
"Leiden University Medical Center (LUMC)": "Netherlands",
"Linkoping University": "Sweden",
"London School of Economics & Political Science": "United Kingdom",
"Loughborough University": "United Kingdom",
"Ludwig Maximilian University of Munich": "Germany",
"Lund University": "Sweden",
"MCI - Internationale Hochschule GmbH": "Austria",
"Maastricht University": "Netherlands",
"Mahidol University": "Thailand",
"Mannheim Business School": "Germany",
"McGill University": "Canada",
"McMaster University": "Canada",
"Meiji University": "Japan",
"Michigan State University": "United States",
"Minzu University of China": "China",
"Monash University": "Australia",
"NOC Bangkok": "Thailand",
"NOC Beijing": "China",
"NOC Chicago": "United States",
"NOC Chongqing": "China",
"NOC Greater Bay Area": "China",
"NOC Indonesia": "Indonesia",
"NOC Israel": "Israel",
"NOC Munich": "Germany",
"NOC Norway": "Norway",
"NOC Paris": "France",
"NOC Philippines": "Philippines",
"NOC Santiago": "Chile",
"NOC Shanghai": "China",
"NOC Shenzhen": "China",
"NOC Silicon Valley": "United States",
"NOC Stockholm": "Sweden",
"NOC Thailand": "Thailand",
"NOC Toronto": "Canada",
"NOC Toronto-Waterloo": "Canada",
"NOC Vietnam": "Vietnam",
"Nagoya University": "Japan",
"Nanjing University": "China",
"Nanyang Technological University": "Singapore",
"National Cheng Kung University": "Taiwan",
"National Chengchi University": "Taiwan",
"National Chiao Tung University": "Taiwan",
"National Taiwan University": "Taiwan",
"National Taiwan University of Science & Technology": "Taiwan",
"National Tsing Hua University": "Taiwan",
"National Yang Ming Chiao Tung University": "Taiwan",
"New York University": "United States",
"Newcastle University": "United Kingdom",
"Northwestern University": "United States",
"Norwegian Sch of Veterinary Science": "Norway",
"Norwegian School of Economics": "Norway",
"Norwegian University of Science and Technology": "Norway",
"Nova School of Business and Economics": "Portugal",
"Oulu University": "Finland",
"Peking University": "China",
"Pennsylvania State University, The": "United States",
"Pohang University of Science and Technology": "South Korea",
"Polytechnic University of Turin": "Italy",
"Princeton University": "United States",
"Purdue University": "United States",
"Queen's University at Kingston": "Canada",
"Queensland University of Technology": "Australia",
"RWTH Aachen University": "Germany",
"Radboud University Nijmegen": "Netherlands",
"Reichman University": "Israel",
"Renmin University of China": "China",
"Rice University": "United States",
"Richard Ivey Sch of Biz, Univ of Western Ontario": "Canada",
"Ritsumeikan University,Kyoto": "Japan",
"Sabanci University": "Turkey",
"San Francisco State University": "United States",
"Sciences Po Paris": "France",
"Seoul National University": "South Korea",
"Shanghai Jiao Tong University": "China",
"Shanghai University of Finance and Economics": "China",
"Simon Fraser University": "Canada",
"Singapore Institute of Technology": "Singapore",
"Singapore Management University": "Singapore",
"Singapore University of Social Sciences": "Singapore",
"Singapore University of Technology and Design": "Singapore",
"Stanford University": "United States",
"Stockholm School of Economics": "Sweden",
"Stockholm University": "Sweden",
"Sungkyunkwan University": "South Korea",
"Suzhou University": "China",
"Swiss Federal Institute of Technology Lausanne": "Switzerland",
"Tallinn University of Technology": "Estonia",
"Tampere University of Technology": "Finland",
"Tec de Monterrey": "Mexico",
"Technical University of Berlin": "Germany",
"Technical University of Darmstadt": "Germany",
"Technical University of Denmark": "Denmark",
"Technical University of Munich": "Germany",
"Telecom Paris": "France",
"Texas A&M University": "United States",
"Thammasat University": "Thailand",
"The Chinese University of Hong Kong (Shenzhen)": "China",
"The LNM Institute of Information Technology": "India",
"The University of Adelaide": "Australia",
"Tianjin University": "China",
"Tianjin University of Finance and Economics": "China",
"Tilburg University": "Netherlands",
"Tohoku University": "Japan",
"Tokyo University of Foreign Studies": "Japan",
"Tokyo University of Marine Science and Technology": "Japan",
"Tongji University": "China",
"Trinity College Dublin": "Ireland",
"Tsinghua University": "China",
"Tulane University": "United States",
"Tunghai University": "Taiwan",
"Ulm University": "Germany",
"Universidad Autonoma de Madrid": "Spain",
"Universita degli Studi di Trento": "Italy",
"Universitat Autonoma de Barcelona": "Spain",
"Universitat Internacional de Catalunya": "Spain",
"Universitat Politecnica de Catalunya": "Spain",
"Universite Catholique De Louvain": "Belgium",
"Universite Grenoble Alpes": "France",
"Universiteit van Stellenbosch": "South Africa",
"University College Cork": "Ireland",
"University College Dublin": "Ireland",
"University College London": "United Kingdom",
"University College Utrecht": "Netherlands",
"University of Aberdeen": "United Kingdom",
"University of Alberta": "Canada",
"University of Amsterdam": "Netherlands",
"University of Antwerp": "Belgium",
"University of Applied Sciences Esslingen": "Germany",
"University of Arizona, The": "United States",
"University of Auckland, The": "New Zealand",
"University of Bath": "United Kingdom",
"University of Birmingham": "United Kingdom",
"University of Bologna": "Italy",
"University of Bonn": "Germany",
"University of Bordeaux": "France",
"University of Bristol": "United Kingdom",
"University of British Columbia (Okanagan), The": "Canada",
"University of British Columbia, The": "Canada",
"University of Brussels, Solvay Business School": "Belgium",
"University of Calgary": "Canada",
"University of California": "United States",
"University of California, Berkeley": "United States",
"University of California, Davis": "United States",
"University of California, Irvine": "United States",
"University of California, Los Angeles": "United States",
"University of California, Merced": "United States",
"University of California, Riverside": "United States",
"University of California, San Diego": "United States",
"University of California, Santa Barbara": "United States",
"University of California, Santa Cruz": "United States",
"University of Cambridge": "United Kingdom",
"University of Canterbury": "New Zealand",
"University of Cologne": "Germany",
"University of Colorado Boulder": "United States",
"University of Commerce 'Luigi Bocconi' Milan": "Italy",
"University of Connecticut": "United States",
"University of Copenhagen": "Denmark",
"University of Delaware": "United States",
"University of Dundee": "United Kingdom",
"University of Edinburgh, The": "United Kingdom",
"University of Florida": "United States",
"University of Freiburg": "Germany",
"University of Geneva": "Switzerland",
"University of Georgia": "United States",
"University of Glasgow": "United Kingdom",
"University of Goteborg": "Sweden",
"University of Gothenburg": "Sweden",
"University of Gottingen": "Germany",
"University of Guelph": "Canada",
"University of Hawaii at Manoa": "United States",
"University of Helsinki": "Finland",
"University of Hohenheim": "Germany",
"University of Hong Kong, The": "Hong Kong",
"University of Iceland": "Iceland",
"University of Illinois Urbana-Champaign": "United States",
"University of Innsbruck": "Austria",
"University of Kaiserslautern, FRG": "Germany",
"University of Konstanz": "Germany",
"University of Lausanne": "Switzerland",
"University of Leeds": "United Kingdom",
"University of Liverpool": "United Kingdom",
"University of Manchester, The": "United Kingdom",
"University of Mannheim": "Germany",
"University of Maryland": "United States",
"University of Melbourne, The": "Australia",
"University of Miami": "United States",
"University of Michigan": "United States",
"University of Minnesota": "United States",
"University of Navarra": "Spain",
"University of New South Wales": "Australia",
"University of Newcastle": "Australia",
"University of North Carolina at Chapel Hill, The": "United States",
"University of North Carolina, Kenan-Flagler": "United States",
"University of Notre Dame": "United States",
"University of Nottingham": "United Kingdom",
"University of Oregon": "United States",
"University of Osaka": "Japan",
"University of Oslo": "Norway",
"University of Otago": "New Zealand",
"University of Ottawa": "Canada",
"University of Oxford": "United Kingdom",
"University of Pennsylvania": "United States",
"University of Pittsburgh": "United States",
"University of Queensland, The": "Australia",
"University of San Diego": "United States",
"University of Seoul": "South Korea",
"University of Sheffield, The": "United Kingdom",
"University of South Carolina": "United States",
"University of Southampton": "United Kingdom",
"University of Southern California": "United States",
"University of Southern Denmark": "Denmark",
"University of St Andrews": "United Kingdom",
"University of St Gallen": "Switzerland",
"University of Strathclyde": "United Kingdom",
"University of Stuttgart": "Germany",
"University of Sydney, The": "Australia",
"University of Technology of Compiegne": "France",
"University of Technology of Troyes": "France",
"University of Texas at Austin, The": "United States",
"University of Tokyo, The": "Japan",
"University of Toronto": "Canada",
"University of Toronto (Mississauga)": "Canada",
"University of Toronto (Scarborough)": "Canada",
"University of Victoria": "Canada",
"University of Virginia": "United States",
"University of Warwick": "United Kingdom",
"University of Washington": "United States",
"University of Waterloo": "Canada",
"University of Western Australia, The": "Australia",
"University of Wisconsin-Madison": "United States",
"University of Wurzburg": "Germany",
"University of York": "United Kingdom",
"University of Zagreb": "Croatia",
"University of Zurich": "Switzerland",
"University of the Republic, Uruguay": "Uruguay",
"Uppsala University": "Sweden",
"Utrecht University": "Netherlands",
"Vanderbilt University": "United States",
"Vassar College": "United States",
"Victoria University": "Australia",
"Victoria University of Wellington": "New Zealand",
"Vienna University of Economics and Business": "Austria",
"Vilnius University": "Lithuania",
"WHU - Otto Beisheim School of Management": "Germany",
"Wageningen University": "Netherlands",
"Warsaw School of Economics": "Poland",
"Warsaw University of Technology": "Poland",
"Waseda University": "Japan",
"Western University": "Canada",
"William & Mary": "United States",
"Xiamen University": "China",
"Yale University": "United States",
"Yonsei University": "South Korea",
"York University": "Canada",
"Zhejiang University": "China",
}


def clean_uni_name(raw: str) -> str:
    name = UNI_ALIASES.get(raw.strip(), raw.strip())
    if name.endswith(", The"):
        name = "The " + name[: -len(", The")]
    name = name.replace(",Seoul", ", Seoul").replace(",Kyoto", ", Kyoto")
    return name


def to_units(v):
    if v is None or v == "":
        return 0
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except (TypeError, ValueError):
        return 0


def to_str(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        # Excel stores all-digit course codes as numbers; 2393.0 should read 2393
        v = int(v)
    s = str(v).strip()
    for bad, good in MOJIBAKE.items():
        s = s.replace(bad, good)
    return s


def course_code(v, partner):
    code = to_str(v)
    if partner == "Technical University of Denmark" and code.lstrip("-").isdigit():
        # DTU codes are five digits; Excel dropped the leading zeros (02393 -> 2393)
        # and a few cells picked up a stray minus sign
        code = code.lstrip("-").zfill(5)
    return code


def mapping_id(r):
    """Stable id for a mapping: a hash of what it maps, so detail-page URLs
    survive a data rebuild. Titles and units are left out so fixing a typo in
    the workbook doesn't change the id."""
    parts = [r["faculty"], r["partnerUni"], r["puCourse1"], r["puCourse2"], r["nusCourse1"], r["nusCourse2"]]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]


def load_course_pages():
    if not COURSE_PAGES.exists():
        return {}
    return json.loads(COURSE_PAGES.read_text(encoding="utf-8"))


def read_rows(wb):
    """Yields (faculty_name, raw partner name, row) for every non-empty row."""
    for sheet_key, faculty_name in FACULTY_NAMES.items():
        for row in wb[sheet_key].iter_rows(min_row=2, values_only=True):
            partner_raw = to_str(row[1])
            if partner_raw:
                yield faculty_name, partner_raw, row


def build_record(faculty_name, partner_raw, row):
    partner = clean_uni_name(partner_raw)
    return {
        "faculty": faculty_name,
        "partnerUni": partner,
        "country": COUNTRY.get(partner_raw, "Other"),
        "puCourse1": course_code(row[2], partner_raw),
        "puCourse1Title": to_str(row[3]),
        "puCrse1Units": to_units(row[4]),
        "puCourse2": course_code(row[5], partner_raw),
        "puCourse2Title": to_str(row[6]),
        "puCrse2Units": to_units(row[7]),
        "nusCourse1": to_str(row[8]).upper(),
        "nusCourse1Title": to_str(row[9]),
        "nusCrse1Units": to_units(row[10]),
        "nusCourse2": to_str(row[11]).upper(),
        "nusCourse2Title": to_str(row[12]),
        "nusCrse2Units": to_units(row[13]),
    }


def main():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    course_pages = load_course_pages()
    records = []
    by_id = {}
    missing_countries = set()
    dropped = 0

    for faculty_name, partner_raw, row in read_rows(wb):
        if partner_raw not in COUNTRY:
            missing_countries.add(partner_raw)
        r = build_record(faculty_name, partner_raw, row)
        if not r["nusCourse1"] and not r["nusCourse2"]:
            dropped += 1  # nothing on the NUS side to map to
            continue
        r["id"] = mapping_id(r)
        if r["id"] in by_id:
            # the workbook lists some mappings twice; keep the first, filling
            # in anything it left blank
            first = by_id[r["id"]]
            for k, v in r.items():
                if v and not first[k]:
                    first[k] = v
            dropped += 1
            continue
        by_id[r["id"]] = r
        for n in ("1", "2"):
            page = course_pages.get(f"{r['partnerUni']}|{r['puCourse' + n]}")
            if page:
                r[f"puCourse{n}Url"] = page["url"]
                if page.get("lang"):
                    r[f"puCourse{n}Lang"] = page["lang"]
        records.append(r)

    if missing_countries:
        print("WARNING: missing country mapping for:", sorted(missing_countries))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(records)} records to {OUT} ({dropped} empty or duplicate rows dropped)")
    print(f"universities: {len(set(r['partnerUni'] for r in records))}")
    print(f"countries: {len(set(r['country'] for r in records))}")
    print(f"verified overseas course pages: {sum(1 for r in records if r.get('puCourse1Url'))}")


if __name__ == "__main__":
    main()
