# postgrad-data

Graduate students in each social science discipline, every year from 1972 to 2025. Built from the
unit-level public-use files of NSF/NCSES's
[Survey of Graduate Students and Postdoctorates in Science and Engineering](https://ncses.nsf.gov/surveys/graduate-students-postdoctorates-s-e/2025) (GSS).

Counts are all graduate students (master's + doctoral, full- + part-time) enrolled each fall at U.S. institutions.
Psychology is reported alongside, since NSF treats it as its own broad field.

## Outputs (`output/`)

| File | Contents |
|---|---|
| `social_science_grad_students.html` | Formatted year x discipline table with notes on series breaks |
| `social_science_grad_students.xlsx` | Same table, plus master's/doctoral split (2017+) and notes |
| `social_science_grad_students_wide.csv` | Year x discipline, all harmonized columns |
| `social_science_grad_students_long.csv` | Year, field, count |
| `social_science_masters_doctoral_2017on.csv` | Master's and doctoral counts by field, 2017 on (not collected before) |

`data/gss_totals_by_year_and_code.csv` holds raw sums for every GSS field code and year, across all fields, not just the social sciences.

## Validation

For every year 1975-2025, the social sciences and psychology totals match NSF's published trend table
(GSS 2025 table 1-14) exactly.

## Series breaks (read before computing trends)

- **1972-74**: fewer institutions surveyed; NSF's own trend tables start in 1975.
- **2007**: survey redesign and field reclassification (this is NSF's "2007new" series).
- **2014**: survey frame grew by 151 institutions, mostly master's-granting ("2014new").
- **2017**: new taxonomy. Through 2016, code 907 "political science" includes international relations,
  public policy *and public administration*. From 2017, IR and public policy have their own codes, and
  public administration is no longer in the survey. Criminology, criminal justice, area/ethnic/gender and urban
  studies sat in "Other social sciences" (910) before they got their own codes.
- **2020**: area/ethnic/gender studies, criminology and urban studies split out of "Other"; history and
  philosophy of science folded into "Other"; human development moved from social sciences to psychology.

## Reproduce

```bash
bash scripts/download_puf.sh                       # ~460 MB of zips into puf/
python scripts/aggregate_puf.py puf data/gss_totals_by_year_and_code.csv
python scripts/build_table.py
python scripts/render_table.py
```

Requires Python with pandas and openpyxl.
