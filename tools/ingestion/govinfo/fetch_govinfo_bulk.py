#!/usr/bin/env python3
"""Enhanced crawler to discover and download govinfo bulk data files.

Supports congress ranges, multiple collections, and full downloads.

Usage: python3 tools/fetch_govinfo_bulk.py --collections BILLS BILLSTATUS --congress-range 93-119 --out /tmp/govinfo --full

This script scrapes govinfo bulkdata directory listings, finds XML files, and downloads samples or full datasets.
It also tries to fetch the `resources` directory for XSD/schema files if present.
"""
import argparse
import os
import time
import sys
import requests
from urllib.parse import urljoin, urlparse
from lxml import html


USER_AGENT = "OpenLegislationFetcher/1.0 (+https://github.com/nysenate/OpenLegislation)"


def get_links(url):
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    doc = html.fromstring(r.content)
    links = doc.xpath("//a[@href]/@href")
    abs_links = [urljoin(url, l) for l in links]
    return abs_links


def filter_xml_links(links):
    xmls = [l for l in links if l.lower().endswith(".xml")]
    return xmls


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def download_file(url, out_dir, session=None):
    session = session or requests.Session()
    headers = {"User-Agent": USER_AGENT}
    local_name = os.path.basename(urlparse(url).path)
    out_path = os.path.join(out_dir, local_name)
    if os.path.exists(out_path):
        print(f"Skipping existing {local_name}")
        return out_path
    print(f"Downloading {url} -> {out_path}")
    with session.get(url, headers=headers, stream=True, timeout=60) as r:
        if r.status_code == 404:
            print("Not found:", url)
            return None
        r.raise_for_status()
        with open(out_path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
    return out_path


def parse_congress_range(congress_range):
    """Parse congress range like '93-119' or '119'"""
    if "-" in congress_range:
        start, end = congress_range.split("-")
        return list(range(int(start), int(end) + 1))
    else:
        return [int(congress_range)]


def crawl_collection(
    base_url,
    collection,
    congresses,
    sessions,
    out_dir,
    samples_per_subdir=3,
    full_download=False,
):
    """Crawl multiple congresses and sessions"""
    sess = requests.Session()
    total_downloaded = 0

    for congress in congresses:
        for session in sessions:
            base = base_url.rstrip("/") + f"/{collection}/{congress}/{session}/"
            print(f"Crawling {collection} {congress}-{session}")
            ensure_dir(out_dir)
            try:
                sublinks = get_links(base)
            except Exception as e:
                print("Failed to fetch base listing", e)
                continue

            # Find subdirectories like hr, s, hres, etc.
            subdirs = [l for l in sublinks if l.endswith("/") and l != base]
            if not subdirs:
                # Sometimes the listing contains just direct files
                subdirs = [base]

            for sd in subdirs:
                print("Scanning subdir", sd)
                try:
                    links = get_links(sd)
                except Exception as e:
                    print("  failed to list", sd, e)
                    continue
                xml_links = filter_xml_links(links)
                print(f"  found {len(xml_links)} xml files")

                if full_download:
                    # Download all files
                    download_count = len(xml_links)
                else:
                    # Download samples
                    download_count = min(samples_per_subdir, len(xml_links))

                for i, xl in enumerate(xml_links):
                    if i >= download_count:
                        break
                    out_path = download_file(xl, out_dir, session=sess)
                    if out_path:
                        total_downloaded += 1
                    time.sleep(1.0)

                # Also try to fetch resources dir for schema
                resources_url = urljoin(sd, "resources/")
                try:
                    res_links = get_links(resources_url)
                    for rl in res_links:
                        if rl.lower().endswith(
                            (".xsd", ".xslt", ".xsl", ".md", ".txt")
                        ):
                            download_file(rl, out_dir, session=sess)
                            time.sleep(0.5)
                except Exception:
                    pass

    print(f"Total files downloaded: {total_downloaded}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collections",
        nargs="+",
        default=["BILLS"],
        help="Collections to download (e.g., BILLS BILLSTATUS BILLSUM)",
    )
    parser.add_argument(
        "--congress-range", default="119", help="Congress range (e.g., 93-119 or 119)"
    )
    parser.add_argument(
        "--sessions", nargs="+", default=["1"], help="Sessions to download (e.g., 1 2)"
    )
    parser.add_argument("--out", default="/tmp/govinfo_bulk", help="Output directory")
    parser.add_argument(
        "--samples", default=3, type=int, help="Samples per subdir (0 for all)"
    )
    parser.add_argument(
        "--full", action="store_true", help="Download all files (not just samples)"
    )

    args = parser.parse_args()

    congresses = parse_congress_range(args.congress_range)
    sessions = [int(s) for s in args.sessions]

    base_url = "https://www.govinfo.gov/bulkdata"

    for collection in args.collections:
        out_dir = os.path.join(args.out, collection.lower())
        samples = 0 if args.full else args.samples
        crawl_collection(
            base_url, collection, congresses, sessions, out_dir, samples, args.full
        )


if __name__ == "__main__":
    main()
