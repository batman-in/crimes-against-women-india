"""Some CII tables are not published as separate files. Extract their pages from the full
Crime in India volume PDFs (downloaded to a temporary folder, not kept) into
data/raw/ncrb_cii_tables/<year>/ and record them in manifest.json.

  2022  Table 5A.4 (SLL part) - Crime in India 2022 Book 1 (Vol I), PDF pages 503-506
  2024  Table 5A.4B (SLL)     - Crime in India 2024 Volume II,      PDF pages 39-42
"""
import json, tempfile
from pathlib import Path
import requests
from pypdf import PdfReader, PdfWriter

HERE = Path(__file__).resolve().parent
RAW = HERE.parent.parent / 'raw' / 'ncrb_cii_tables'
UA = {'User-Agent': 'Mozilla/5.0 (research data download)'}

JOBS = [
    (2022, '5A.4', 'Juveniles Apprehended - SLL Crimes (Crime Head, Age Group & Gender-wise) - 2022 [pages 503-506 of CII 2022 Book 1]',
     'https://www.ncrb.gov.in/uploads/nationalcrimerecordsbureau/custom/1701607577CrimeinIndia2022Book1.pdf', 503, 506,
     'CII2022_Book1_p503-506_Table5A4_SLL.pdf'),
    (2024, '5A.4', 'Juveniles Apprehended - SLL Crimes (Crime Head, Age Group & Gender-wise) - 2024 [pages 39-42 of CII 2024 Volume II]',
     'https://www.ncrb.gov.in/uploads/files/2CrimeinIndia2024-VolumeII.pdf', 39, 42,
     'CII2024_VolII_p39-42_Table5A4B_SLL.pdf'),
]


def main():
    man_p = RAW / 'manifest.json'
    man = json.loads(man_p.read_text(encoding='utf8'))
    have = {m['local'] for m in man}
    with tempfile.TemporaryDirectory() as tmp:
        for year, tid, title, url, a, b, fn in JOBS:
            out = RAW / str(year) / fn
            if not out.exists():
                src = Path(tmp) / url.split('/')[-1]
                if not src.exists():
                    with requests.get(url, headers=UA, timeout=600, stream=True) as r:
                        r.raise_for_status()
                        with open(src, 'wb') as fh:
                            for chunk in r.iter_content(1 << 20):
                                fh.write(chunk)
                rd, wr = PdfReader(src), PdfWriter()
                for i in range(a - 1, b):
                    wr.add_page(rd.pages[i])
                with open(out, 'wb') as fh:
                    wr.write(fh)
                print('wrote', out.name)
            local = str(year) + chr(92) + fn
            if local not in have:
                man.append({'year': year, 'table': tid, 'title': title, 'url': url, 'pages': f'{a}-{b}',
                            'local': local, 'bytes': out.stat().st_size})
    man_p.write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding='utf8')


if __name__ == '__main__':
    main()
