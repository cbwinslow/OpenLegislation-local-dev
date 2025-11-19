#!/usr/bin/env python3
"""Parse govinfo bulk XML samples and emit JSON lines matching `source_documents` fields.

Usage: python3 tools/govinfo_parse_to_json.py /tmp/govinfo_samples > samples.jsonl
"""
import sys
import os
import re
import json
import base64
from lxml import etree
import signal


def safe_text(node):
    if node is None:
        return None
    text = "".join(node.itertext()).strip()
    return text if text else None


def first_xpath_text(tree, paths):
    for p in paths:
        res = tree.xpath(p)
        if not res:
            continue
        if isinstance(res, list):
            n = res[0]
            return safe_text(n)
        else:
            return str(res)
    return None


def extract_sponsors(tree):
    sponsors = []
    # common sponsor xpaths (try a few common locations and dedupe)
    nodes = tree.xpath(
        "//sponsor | //sponsors//sponsor | //sponsor-name | //sponsorList//sponsor | //sponsor_name"
    )
    seen = set()
    for n in nodes:
        name = safe_text(n)
        if not name:
            # sometimes sponsor is nested like <sponsor><name>..</name></sponsor>
            nn = n.xpath(".//name")
            if nn:
                name = safe_text(nn[0])
        if name and name not in seen:
            seen.add(name)
            sponsors.append({"name": name})
    return sponsors


def extract_actions(tree):
    acts = []
    nodes = tree.xpath("//action | //actions//action | //history//action")
    for n in nodes:
        date = first_xpath_text(n, ["./@date", "./date", ".//date"])
        # prefer a short summary: look for <type> or <text> children, else collapse and truncate
        summary = first_xpath_text(n, ["./type", ".//type", "./text", ".//text"])
        if not summary:
            summary = safe_text(n)
        if summary:
            # truncate very long action descriptions
            if len(summary) > 300:
                summary = summary[:300].rsplit(" ", 1)[0] + "..."
        acts.append({"date": date, "description": summary})
    return acts


def parse_file(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    try:
        parser = etree.XMLParser(recover=True)
        tree = etree.fromstring(raw, parser=parser)
    except Exception:
        # fallback to parsing as HTML-ish
        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(raw, parser=parser)
        except Exception as e:
            print("Failed to parse", path, e, file=sys.stderr)
            return None

    # wrap tree with ElementTree-like interface for xpath
    class T:
        def __init__(self, el):
            self.el = el

        def xpath(self, p):
            return self.el.xpath(p)

    t = T(tree)

    basename = os.path.basename(path)
    m = re.match(r"BILLS-(\d+)([a-zA-Z]+)\d+.*\.xml", basename)
    congress = m.group(1) if m else None
    bill_type = m.group(2) if m else None

    # reconstruct a likely source_url used by govinfo
    name_noext = basename[:-4]
    source_url = f"https://www.govinfo.gov/content/pkg/{name_noext}/xml/{basename}"

    title = first_xpath_text(
        t,
        [
            "//official-title",
            "//officialTitle",
            "//title//official-title",
            "//title",
            "//bill-title",
            "//billTitle",
        ],
    )

    short_title = first_xpath_text(
        t, ["//short-title", "//shortTitle", "//shortTitleText"]
    )

    introduced = first_xpath_text(
        t,
        [
            "//introduced-date",
            "//introducedDate",
            "//introduced",
            "//history//introduced",
        ],
    )

    sponsors = extract_sponsors(t)
    actions = extract_actions(t)

    record = {
        "source_domain": "govinfo.gov",
        "source_collection": "BILLS",
        "source_congress": congress,
        "source_session": None,
        "source_filename": basename,
        "source_url": source_url,
        "doc_type": bill_type,
        "published_at": introduced,
        "received_at": None,
        "canonical_id": name_noext,
        "title": title or short_title,
        "sponsors": sponsors or None,
        "actions": actions or None,
        "text_versions": None,
        "raw_xml_base64": base64.b64encode(raw).decode("ascii"),
    }
    # parsed_json holds the extracted fields for quick indexing
    record["parsed_json"] = {
        "title": record["title"],
        "sponsors": record["sponsors"],
        "actions": record["actions"],
    }
    return record


def main():
    if len(sys.argv) < 2:
        print("Usage: govinfo_parse_to_json.py /path/to/samplesdir", file=sys.stderr)
        sys.exit(2)
    in_dir = sys.argv[1]
    # Make SIGPIPE not raise exceptions when piping to tools like `head`
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except Exception:
        pass
    for fn in sorted(os.listdir(in_dir)):
        if not fn.lower().endswith(".xml"):
            continue
        path = os.path.join(in_dir, fn)
        rec = parse_file(path)
        if rec:
            try:
                print(json.dumps(rec, ensure_ascii=False))
            except BrokenPipeError:
                # consumer (e.g. head) closed the pipe; exit quietly
                try:
                    sys.stdout.close()
                except Exception:
                    pass
                sys.exit(0)


if __name__ == "__main__":
    main()
