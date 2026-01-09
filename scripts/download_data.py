#!/usr/bin/env python3
"""
This file was used to download the OGC WKT data from the previous version of spatialreference.org.
It should not be used once spatialreference.org is upgraded to the new version.
This code is kept here only for archival/tracking purposes.
"""

import requests
import json
import html
import time
from bs4 import BeautifulSoup
from pathlib import Path


def fetch_page(domain: str, page: int, session: requests.Session):
    """Fetch a single page of spatial references for a given domain."""
    page_url = f'https://spatialreference.org/ref/{domain}/?page={page}'
    try:
        response = session.get(page_url, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching page {page_url}: {e}")
        return None


def parse_page(domain: str, html_text: str):
    """Extract (code, name) pairs from a single HTML page."""
    soup = BeautifulSoup(html_text, 'html.parser')
    results = []
    for li in soup.select('li a[href^="/ref/"]'):
        href = li.get('href', '')
        if f'/ref/{domain}/' in href:
            code = href.strip('/').split('/')[-1]
            name = li.get_text(strip=True)
            # Some items show as "code: name", ensure we keep readable part
            name = html.unescape(name)
            results.append((code, name))
    return results


def fetch_ogcwkt(domain: str, code: str, session: requests.Session):
    """Fetch the OGC WKT data for a specific code."""
    url = f'https://spatialreference.org/ref/{domain}/{code}/ogcwkt/'
    try:
        response = session.get(url, timeout=15)
        if response.ok:
            return response.text.strip()
        else:
            print(f"Failed to fetch OGCWKT for {domain}/{code}: HTTP {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching OGCWKT for {domain}/{code}: {e}")
    return None


if __name__ == '__main__':

    msg = """
This file was used to download the OGC WKT data from the previous version of spatialreference.org.
It should not be used once spatialreference.org is upgraded to the new version.
This code is here just to track it.
"""
    print(msg)
    # Comment out the next line if you actually want to run the scraper
    # exit(1)

    # --- Scraping starts here ---
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; spatialref-downloader/1.0)'}
    session = requests.Session()
    session.headers.update(headers)

    for domain_upper_case in ['IAU2000', 'SR-ORG']:
        results = []
        domain = domain_upper_case.lower()

        print(f"\n=== Processing domain: {domain_upper_case} ===")
        for page in range(1, 70):  # 70 is a safe upper limit; real count is below 60
            html_text = fetch_page(domain, page, session)
            if not html_text:
                continue

            entries = parse_page(domain, html_text)
            print(f"Page {page}: found {len(entries)} entries")
            if len(entries) == 0:
                print(f"Done! Last page was #{page - 1}")
                break

            for code, name in entries:
                print(f"  - {code}: {name}")
                record = {'auth_name': domain_upper_case, 'code': str(code), 'name': name}

                ogcwkt = fetch_ogcwkt(domain, code, session)
                if ogcwkt:
                    record['ogcwkt'] = ogcwkt

                results.append(record)
                time.sleep(0.3)  # polite delay between requests

            time.sleep(1)  # wait before next page

        # --- Save results ---
        output_path = Path(f'{domain}.json')
        with output_path.open('w', encoding='utf-8') as fp:
            json.dump(results, fp, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(results)} entries to {output_path}")

    print("\nAll domains processed successfully.")
    exit(0)
