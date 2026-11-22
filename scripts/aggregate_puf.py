import zipfile, sys, os, io, pandas as pd, tempfile
zdir, out = sys.argv[1], sys.argv[2]
rows = []
for f in sorted(os.listdir(zdir)):
    if not f.endswith('.zip'): continue
    z = zipfile.ZipFile(os.path.join(zdir, f))
    sas = [n for n in z.namelist() if n.lower().endswith('.sas7bdat')]
    for n in sas:
        with tempfile.TemporaryDirectory() as td:
            p = z.extract(n, td)
            df = pd.read_sas(p, encoding='latin1')
        df.columns = [c.lower() for c in df.columns]
        need = ['year','gss_code','pt_tot_all_races_v','ft_tot_all_races_v']
        miss = [c for c in need if c not in df.columns]
        if miss:
            print(f, n, 'MISSING', miss, list(df.columns)[:30]); continue
        extra = [c for c in ['ma_pt_tot_all_races_v','dr_pt_tot_all_races_v','ma_ft_tot_all_races_v','dr_ft_tot_all_races_v'] if c in df.columns]
        g = df[need+extra].copy()
        g['gss_code'] = g['gss_code'].astype(str).str.strip()
        g['year'] = g['year'].astype(str).str.strip()
        a = g.groupby(['year','gss_code'])[need[2:]+extra].sum(min_count=1).reset_index()
        a['file'] = f; a['n_units'] = g.groupby(['year','gss_code']).size().values
        rows.append(a)
        print(f, n, len(df), sorted(g['year'].unique()))
pd.concat(rows).to_csv(out, index=False)
