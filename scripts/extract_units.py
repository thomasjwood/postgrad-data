"""Stack the GSS public-use files (1972-2025) into one unit-level file of graduate student counts.

One row per year x school x GSS code. Keeps identifiers, institution/school attributes and the
graduate-student count variables (total, sex, enrollment intensity, first-time, master's/doctoral).
Race/ethnicity, financial support and postdoc/NFR detail stay in the raw files (see scripts/puf_urls.txt).
Writes one uncompressed CSV per decade (e.g. gss_units_1970s.csv) to the output directory.
Usage: python extract_units.py <dir of GSS zips> <out dir>
"""
import os, re, sys, zipfile, tempfile
import pandas as pd

ID = ["year", "institution_id", "unitid", "institution_name", "school_id", "full_school_name",
      "school_type_code", "toc_code", "institution_state", "hdg_inst", "hdg_code",
      "carnegie_code_2015", "hbcu_flag", "gss_code"]
pat = re.compile(r"^(ma_|dr_)?(pt|ft)_(tot|men|wmen)_all_races_v$|^(ma_|dr_)?ft_frst_(tot|men|wmen)_all_races_v$")

frames = []
for f in sorted(os.listdir(sys.argv[1])):
    if not f.endswith(".zip"):
        continue
    z = zipfile.ZipFile(os.path.join(sys.argv[1], f))
    n = [x for x in z.namelist() if x.lower().endswith("_code.sas7bdat")][0]
    with tempfile.TemporaryDirectory() as td:
        df = pd.read_sas(z.extract(n, td), encoding="latin1")
    df.columns = [c.lower() for c in df.columns]
    keep = [c for c in ID if c in df.columns] + sorted(c for c in df.columns if pat.match(c))
    d = df[keep].copy()
    for c in ("year", "gss_code"):
        d[c] = d[c].astype(str).str.strip()
    frames.append(d)
    print(f, len(d), len(keep))
out = pd.concat(frames, ignore_index=True)
num = [c for c in out.columns if pat.match(c)]
out[num] = out[num].astype("Int64")
os.makedirs(sys.argv[2], exist_ok=True)
dec = out.year.str[:3]
for d_, part in out.groupby(dec):
    part.to_csv(os.path.join(sys.argv[2], f"gss_units_{d_}0s.csv"), index=False)
print(out.shape)
