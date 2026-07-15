# NSE UDiFF Bhavcopy Downloader — GitHub Actions साठी
import requests, zipfile, io, csv, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/"
}

def download_for_date(d):
    ds = d.strftime("%Y%m%d")
    url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{ds}_F_0000.csv.zip"
    print(f"Trying: {url}")
    r = requests.get(url, headers=HEADERS, timeout=90)
    if r.status_code == 200 and len(r.content) > 1000:
        return r.content
    return None

def main():
    # IST वेळेनुसार आजची तारीख
    d = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    # शनिवार/रविवार असेल तर मागचा शुक्रवार
    while d.weekday() >= 5:
        d -= timedelta(days=1)

    content = None
    # Holiday असेल तर मागील 7 दिवसांपर्यंत मागे जाऊन बघा
    for _ in range(7):
        content = download_for_date(d)
        if content:
            break
        d -= timedelta(days=1)
        while d.weekday() >= 5:
            d -= timedelta(days=1)

    if not content:
        print("ERROR: Bhavcopy मिळाली नाही")
        sys.exit(1)

    # Zip मधून CSV काढा
    zf = zipfile.ZipFile(io.BytesIO(content))
    csv_name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
    raw = zf.read(csv_name).decode("utf-8", errors="ignore")

    reader = csv.DictReader(io.StringIO(raw))
    out_rows = []
    for row in reader:
        # UDiFF column names
        if (row.get("SctySrs") or "").strip() == "EQ":
            out_rows.append([
                (row.get("TckrSymb") or "").strip(),   # Symbol
                "EQ",                                   # Series
                (row.get("ClsPric") or "").strip(),     # Close Price
                (row.get("TtlTradgVol") or "").strip(), # Today Volume
                (row.get("TtlTrfVal") or "").strip()    # Value Traded
            ])

    import os
    os.makedirs("data", exist_ok=True)
    with open("data/latest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Symbol", "Series", "ClosePrice", "TodayVolume", "ValueTraded", d.strftime("%Y-%m-%d")])
        w.writerows(out_rows)

    print(f"Done: {len(out_rows)} EQ stocks, date {d}")

if __name__ == "__main__":
    main()
