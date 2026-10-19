#!/usr/bin/env python3
"""diagnose.py - which problem is holding a video back, from its Studio numbers.

    python3 diagnose.py --impressions 47200 --ctr 0.5 --views 347 --length 14:00 \
                        --search-share 4 --playlist-share 65 --avd 3:10

Prints the bottleneck first, then what to do about it. It reads only numbers you give it (from
Studio > the video > Analytics) and invents none. The thresholds are rules of thumb: pass
--channel-ctr (your channel's usual click-through %) to judge against your own baseline instead of a
generic one.

Order of the checks matters. A video is first limited by whether it is SHOWN (impressions), then by
whether it is CLICKED (click-through rate), then by whether people STAY (average view duration).
Fixing a later stage before an earlier one wastes the work.
"""
import sys


def arg(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def secs(s):
    if s is None:
        return None
    sec = 0.0
    for p in str(s).split(":"):
        sec = sec * 60 + float(p)
    return sec


def main():
    a = sys.argv[1:]
    if "--impressions" not in a or "--ctr" not in a:
        print(__doc__)
        sys.exit(1)
    imp = float(arg(a, "--impressions"))
    ctr = float(arg(a, "--ctr"))
    views = arg(a, "--views")
    length = secs(arg(a, "--length"))
    avd = secs(arg(a, "--avd"))
    search = arg(a, "--search-share")
    playlist = arg(a, "--playlist-share")
    base = float(arg(a, "--channel-ctr", 4.0))
    age = arg(a, "--age-days")

    findings = []

    if age is not None and float(age) >= 14 and imp < 500:
        findings.append((1, "NOT SHOWN",
                         f"Only {imp:,.0f} impressions after {age} days. YouTube is not testing this video on "
                         "viewers. Work on discoverability first: topic wording in the title, a clear series/playlist "
                         "position, tags that match real searches, and chapters."))

    if imp >= 1000 and ctr < base * 0.5:
        findings.append((2, "NOT CLICKED",
                         f"{imp:,.0f} impressions but {ctr:g}% click-through (baseline {base:g}%). People see it and "
                         "pass. Change the title and thumbnail, not the tags. The thumbnail must say what THIS "
                         "video is about; a thumbnail shared across a whole series cannot."))
    elif imp >= 1000 and ctr < base:
        findings.append((3, "CLICK RATE BELOW BASELINE",
                         f"Click-through {ctr:g}% is under your {base:g}% baseline. A sharper title or a "
                         "topic-specific thumbnail is the cheapest test."))

    if avd is not None and length:
        ratio = avd / length
        low = 0.15 if length >= 1800 else 0.25
        if ratio < low:
            findings.append((4, "NOT WATCHED",
                             f"Average view duration is {ratio:.0%} of the video. Metadata will not fix this: look at "
                             "the retention graph and the first 30 seconds, and cut or restructure."))

    if search is not None and playlist is not None and float(playlist) >= 50 and float(search) < 10:
        findings.append((5, "AUDIENCE MIX",
                         f"{float(playlist):g}% of views come from the playlist and only {float(search):g}% from "
                         "search. These impressions are mostly your existing audience, so title and thumbnail "
                         "matter more than keywords here."))

    if not findings:
        print("No blocking problem found in these numbers. Re-check after 14 days with more data.")
        return

    findings.sort()
    print("BOTTLENECK FIRST\n")
    for _, tag, text in findings:
        print(f"[{tag}] {text}\n")
    if views is not None:
        print(f"(views so far: {views})")


if __name__ == "__main__":
    main()
