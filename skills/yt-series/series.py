#!/usr/bin/env python3
"""series.py - audit a playlist or series for the problems that make every video look the same.

    python3 series.py --playlist PL4yL5rqgtVtpCBRHBOgeV762beQ2o6Wkt --thumbs
    python3 series.py --file videos.tsv --thumbs          # lines: video_id<TAB>title[<TAB>description]

Checks, all deterministic:
  * titles with no topic: after removing the series words (channel name, "Striver's DSA Sheet",
    "DSA in 50 days"...) no meaningful word remains, so a viewer cannot tell videos apart
  * numbering: duplicate and missing episode numbers (the first "#N" in each title)
  * identical thumbnails (--thumbs): downloads each thumbnail and groups byte-identical ones. A whole
    series sharing one image gives viewers no reason to pick one episode over another
  * descriptions (file mode with a third column): empty, or missing the playlist link

--playlist reads YouTube's public playlist page, which returns the first 100 videos only. For longer
playlists use --file. --series-words adds comma-separated words to ignore when judging topics.
"""
import hashlib, json, re, sys, time, urllib.request

DEFAULT_SERIES = ("dsa striver striver's sheet solving python by in days using vinay mishra series day "
                  "leetcode gfg geeks for the of with and sde one shot").split()
UA = {"User-Agent": "Mozilla/5.0"}


def arg(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()


def walk(node, out):
    if isinstance(node, dict):
        r = node.get("playlistVideoRenderer")
        if r:
            runs = (r.get("title") or {}).get("runs") or []
            out.append((r.get("videoId"), "".join(x.get("text", "") for x in runs)))
        lk = node.get("lockupViewModel")
        if lk and "VIDEO" in str(lk.get("contentType", "")):
            title = (((lk.get("metadata") or {}).get("lockupMetadataViewModel") or {}).get("title") or {}).get("content", "")
            out.append((lk.get("contentId"), title))
        for v in node.values():
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


def from_playlist(pid):
    html = fetch("https://www.youtube.com/playlist?list=" + pid).decode("utf-8", "replace")
    m = re.search(r"ytInitialData\s*=\s*(\{.+?\});\s*</script>", html, re.S)
    if not m:
        raise RuntimeError("could not find playlist data; use --file instead")
    out = []
    walk(json.loads(m.group(1)), out)
    return [(vid, title, "") for vid, title in out if vid]


def from_file(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2 and parts[0].strip():
            rows.append((parts[0].strip(), parts[1].strip(), parts[2].strip() if len(parts) > 2 else ""))
    return rows


def episode(title):
    m = re.search(r"#\s*0*(\d+)", title)
    return int(m.group(1)) if m else None


def topic_words(title, series):
    words = re.findall(r"[A-Za-z][A-Za-z']{2,}", re.sub(r"#\s*\d+", " ", title))
    return [w for w in words if w.lower() not in series]


def main():
    a = sys.argv[1:]
    if "--playlist" not in a and "--file" not in a:
        print(__doc__)
        sys.exit(1)
    series = set(DEFAULT_SERIES) | {w.strip().lower() for w in arg(a, "--series-words", "").split(",") if w.strip()}
    try:
        rows = from_playlist(arg(a, "--playlist")) if "--playlist" in a else from_file(arg(a, "--file"))
    except Exception as e:
        print(f"could not load videos: {e}")
        sys.exit(2)
    print(f"{len(rows)} videos\n")

    topicless = [(v, t) for v, t, _ in rows if not topic_words(t, series)]
    print(f"[TITLES] {len(topicless)} with no topic:")
    for v, t in topicless[:40]:
        print(f"   {v}  {t[:70]}")
    if len(topicless) > 40:
        print(f"   ... and {len(topicless) - 40} more")

    nums = [episode(t) for _, t, _ in rows]
    present = [n for n in nums if n is not None]
    dupes = sorted({n for n in present if present.count(n) > 1})
    missing = sorted(set(range(1, max(present) + 1)) - set(present)) if present else []
    print(f"\n[NUMBERING] duplicates: {dupes or 'none'}; missing: {missing or 'none'}")
    if "--playlist" in a and len(rows) >= 100:
        print("   note: the playlist page returns at most 100 videos, so 'missing' may just be the cut-off; use --file")

    if any(d for _, _, d in rows):
        empty = [v for v, _, d in rows if not d.strip()]
        noplay = [v for v, _, d in rows if d.strip() and "playlist?list=" not in d]
        print(f"\n[DESCRIPTIONS] empty: {len(empty)}; without the playlist link: {len(noplay)}")

    if "--thumbs" in a:
        limit = int(arg(a, "--limit", "1000"))
        groups = {}
        for v, _, _ in rows[:limit]:
            try:
                h = hashlib.sha1(fetch(f"https://i.ytimg.com/vi/{v}/hqdefault.jpg")).hexdigest()
            except OSError:
                continue
            groups.setdefault(h, []).append(v)
            time.sleep(0.05)
        biggest = max(groups.values(), key=len) if groups else []
        print(f"\n[THUMBNAILS] checked {sum(len(g) for g in groups.values())}; "
              f"{len(groups)} distinct images; the most-shared image is used on {len(biggest)} videos")
        if len(biggest) > 1:
            print("   a thumbnail repeated across episodes cannot tell a viewer which episode is which")


if __name__ == "__main__":
    main()
