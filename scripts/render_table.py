"""Render output/social_science_grad_students_wide.csv as a formatted HTML table and an Excel workbook."""
import pandas as pd

w = pd.read_csv("output/social_science_grad_students_wide.csv", index_col=0)
w["Criminology & criminal justice"] = w[["Criminal justice", "Criminology"]].sum(axis=1, min_count=1)
w = w.rename(columns={"Political science": "Political science (as reported)"})
h = pd.read_csv("output/polisci_harmonized.csv", index_col=0)
w["Political science (harmonized)"] = h.political_science.round()
cols = ["Political science (harmonized)", "Political science (as reported)", "International relations", "Public policy", "Economics",
        "Agricultural economics", "Sociology", "Anthropology", "Sociology/anthropology (combined)",
        "Geography", "Linguistics", "Criminology & criminal justice", "Area, ethnic & gender studies",
        "Urban studies", "History & philosophy of science", "Human development",
        "Other social sciences", "Social sciences, total", "Psychology"]
w = w[cols]

# series breaks: marker shown next to the year
breaks = {1975: "a", 2007: "b", 2014: "c", 2017: "d", 2020: "e"}
notes = {
    "a": "1972&ndash;74 cover fewer institutions; NSF's published trend tables start in 1975.",
    "b": "2007: survey redesign and field reclassification (NSF's \"2007new\" series).",
    "c": "2014: survey frame expanded by 151 institutions, mostly master's-granting (NSF's \"2014new\").",
    "d": "2017: new field taxonomy. Through 2016, political science includes international relations, "
         "public policy and public administration; from 2017 these are split out and public administration "
         "is no longer counted. Criminology, area/ethnic/gender and urban studies sat in \"Other\" before "
         "they got their own codes.",
    "e": "2020: area/ethnic/gender studies, criminology and urban studies split from \"Other\"; history and "
         "philosophy of science folded into \"Other\"; human development moved to psychology.",
    "h": "Political science (harmonized): through 2016, each institution's combined political science/IR/public "
         "policy/public administration count is split by its IPEDS master's and doctoral completions in those four "
         "fields (completions in the five years from that fall, master's weighted 2, doctorates 6). Tested on "
         "2017&ndash;2025, where NSF reports the fields separately, the national estimate is within about 2% each "
         "year. From 2017 it is NSF's reported count. Before 1984 it relies on IPEDS 1980 and 1984 only.",
}

def fmt(v):
    return "" if pd.isna(v) else f"{int(v):,}"

short = {"Sociology/anthropology (combined)": "Soc./anthro. (combined)"}
head = "".join(f"<th>{short.get(c, c)}{"<sup>h</sup>" if "harmonized" in c else ""}</th>" for c in cols)
body = []
for y, r in w.iterrows():
    cls = ' class="brk"' if y in breaks and y != 1975 else ""
    mark = f"<sup>{breaks[y]}</sup>" if y in breaks else ""
    tds = "".join(f'<td class="{"tot" if c.startswith(("Social sciences", "Political science (harm")) else ""}">{fmt(r[c])}</td>' for c in cols)
    body.append(f"<tr{cls}><th>{y}{mark}</th>{tds}</tr>")

html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Graduate students in the social sciences, 1972-2025</title>
<style>
body {{ font-family: "Public Sans", "Roboto", system-ui, sans-serif; margin: 2rem; color: #222; }}
h1 {{ font-size: 1.3rem; margin: 0 0 .2rem; }}
p.sub {{ margin: 0 0 1rem; color: #555; font-size: .9rem; }}
table {{ border-collapse: collapse; font-size: .78rem; font-variant-numeric: tabular-nums; }}
thead th {{ position: sticky; top: 0; background: #f2f2f2; vertical-align: bottom; padding: .4rem .35rem;
           font-weight: 600; text-align: right; max-width: 6.5rem; border-bottom: 2px solid #999; }}
tbody th {{ text-align: left; padding: .15rem .6rem .15rem .3rem; font-weight: 600; }}
td {{ text-align: right; padding: .15rem .35rem; }}
tbody tr:nth-child(even) {{ background: #fafafa; }}
tr.brk td, tr.brk th {{ border-top: 1.5px solid #777; }}
td.tot {{ font-weight: 600; background: #f2f2f2; }}
.notes {{ font-size: .78rem; color: #444; max-width: 70rem; margin-top: 1rem; }}
</style></head><body>
<h1>Graduate students in the social sciences, by discipline, 1972&ndash;2025</h1>
<p class="sub">Master's and doctoral students, full- and part-time, at U.S. institutions, fall of each year.
Psychology is a separate broad field in the NSF data.</p>
<table><thead><tr><th style="text-align:left">Year</th>{head}</tr></thead>
<tbody>{''.join(body)}</tbody></table>
<div class="notes">{''.join(f'<p><sup>{k}</sup> {v}</p>' for k, v in notes.items())}
<p>Source: NSF/NCSES Survey of Graduate Students and Postdoctorates in Science and Engineering (GSS), public-use files 1972&ndash;2025.</p></div>
</body></html>"""
open("output/social_science_grad_students.html", "w", encoding="utf-8").write(html)

with pd.ExcelWriter("output/social_science_grad_students.xlsx", engine="openpyxl") as xw:
    w.to_excel(xw, sheet_name="By discipline")
    pd.read_csv("output/social_science_masters_doctoral_2017on.csv").to_excel(
        xw, sheet_name="Masters-doctoral 2017+", index=False)
    pd.DataFrame({"note": [f"{k}: " + v.replace("&ndash;", "-") for k, v in notes.items()]}).to_excel(
        xw, sheet_name="Notes", index=False)
    ws = xw.sheets["By discipline"]
    ws.freeze_panes = "B2"
    for col in ws.iter_cols(min_col=2):
        for c in col[1:]:
            c.number_format = "#,##0"
        ws.column_dimensions[col[0].column_letter].width = 14
print("ok")
