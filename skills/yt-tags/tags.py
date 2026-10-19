#!/usr/bin/env python3
"""tags.py - YouTube tags that always fit, counted exactly the way Studio counts them.

    python3 tags.py count "tag one,tag two"                 # or: count --file tags.txt
    python3 tags.py fit --existing "a,b" --add "x,y,z"      # keep existing, add while it fits
    python3 tags.py suggest --seed "system design,fifa 26"  # real search phrases, ranked, fitted
                                                             # add --avoid "java,c++" to drop other languages
                                                             # add --require "leetcode,python,dsa" when a seed is ambiguous
                                                             # ("sliding window" alone suggests house windows)

Studio's limit is 500 and the counter is NOT a plain character count. Verified against Studio's own
counter (442/500 for 27 tags, 500/500 for 29 tags):

    total = sum(len(tag)) + (number_of_tags - 1) commas + 2 for every tag that contains a space

A tag with a space is stored in quotes, which is where the extra 2 comes from. Over 500 and Studio
refuses to save ("Cannot save until errors are resolved"), so every path here ends in `fit`.

`suggest` asks YouTube's own search autocomplete what people type after your seed phrases. That is
search demand, not a promise of views: use it to pick words people really use, not to stuff.
"""
import json, re, sys, time, urllib.parse, urllib.request

LIMIT = 500
EXPAND = ["", " for", " in", " vs", " interview", " explained"]


def clean(tag):
    tag = re.sub(r"[<>,\"]", " ", tag)
    return re.sub(r"\s+", " ", tag).strip().lower()


def parse(text):
    seen, out = set(), []
    for raw in text.split(","):
        t = clean(raw)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def cost(tag):
    return len(tag) + (2 if " " in tag else 0)


def total(tags):
    return sum(cost(t) for t in tags) + max(len(tags) - 1, 0)


def fit(existing, extra, limit=LIMIT):
    """Existing tags are never touched. Extras are added in order, only while the total stays <= limit."""
    kept, skipped = list(existing), []
    have = set(kept)
    for t in extra:
        if t in have:
            continue
        if total(kept + [t]) <= limit:
            kept.append(t)
            have.add(t)
        else:
            skipped.append(t)
    return kept, skipped


def report(tags, skipped=()):
    print(",".join(tags))
    print(f"\nStudio will show {total(tags)}/{LIMIT}  ({len(tags)} tags)")
    if skipped:
        print("did not fit: " + ", ".join(skipped))


def autocomplete(query):
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "ds": "yt", "q": query})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return [clean(s) for s in data[1]] if len(data) > 1 else []


def suggest(seeds, existing, max_new, avoid=(), require=()):
    score = {}
    for seed in seeds:
        words = set(seed.split())
        for suffix in EXPAND:
            for rank, s in enumerate(autocomplete(seed + suffix)):
                if not s or not (words & set(s.split())):
                    continue
                score[s] = score.get(s, 0) + max(10 - rank, 1)
            time.sleep(0.3)
    ranked = [s for s, _ in sorted(score.items(), key=lambda kv: (-kv[1], len(kv[0])))
              if s not in existing and len(s) <= 60 and not any(w in s.split() for w in avoid)
              and (not require or any(w in s for w in require))]
    return ranked[:max_new * 3], score


def arg(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("count", "fit", "suggest"):
        print(__doc__)
        sys.exit(1)
    cmd, a = a[0], a[1:]
    if cmd == "count":
        text = open(arg(a, "--file"), encoding="utf-8").read().replace("\n", ",") if "--file" in a else \
            " ".join(x for x in a if not x.startswith("--"))
        tags = parse(text)
        print(f"{total(tags)}/{LIMIT}  ({len(tags)} tags)  " + ("OK" if total(tags) <= LIMIT else "TOO LONG - Studio will not save"))
        sys.exit(0 if total(tags) <= LIMIT else 2)
    existing = parse(arg(a, "--existing", ""))
    if cmd == "fit":
        kept, skipped = fit(existing, parse(arg(a, "--add", "")))
        report(kept, skipped)
        return
    seeds = parse(arg(a, "--seed", ""))
    if not seeds:
        print("suggest needs --seed")
        sys.exit(1)
    try:
        ranked, score = suggest(seeds, existing, int(arg(a, "--max-new", "8")),
                                parse(arg(a, "--avoid", "")), parse(arg(a, "--require", "")))
    except OSError as e:
        print(f"could not reach YouTube autocomplete: {e}")
        sys.exit(2)
    kept, skipped = fit(existing, ranked[:int(arg(a, "--max-new", "8"))])
    print("ranked by autocomplete demand:")
    for s in ranked[:int(arg(a, "--max-new", "8")) * 2]:
        print(f"  {score[s]:>3}  {s}")
    print()
    report(kept, skipped)


if __name__ == "__main__":
    main()
