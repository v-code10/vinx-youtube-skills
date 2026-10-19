#!/usr/bin/env python3
"""midroll.py - target break marks for a video, so YouTube has natural breakpoints to place ads on.

Use the output as EDITING MARKS (end a section with a clear beat and a short pause there), not as
ad times to type into Studio: YouTube flagged evenly spaced manual slots as unlikely to show ads.

    python3 midroll.py --duration 58:03
    python3 midroll.py --duration 20:00 --mode balanced
    python3 midroll.py --duration 58:03 --srt transcript.srt --chapters "0:00,6:10,14:30"
    python3 midroll.py --duration 12:00 --first 120 --gap 240

Prints the break marks and the matching Studio time format (MM:SS:FF) in case a manual slot is
wanted at a real pause.

The count comes from one formula, so it scales with any length:

    ads = floor((duration - 60s tail - first) / gap) + 1

Modes set (first, gap). `earn` is the default: first ad at 1:30, then one every 4:00, which is
5 ads in a 20-minute video (1:30, 5:30, 9:30, 13:30, 17:30).

    earn      first 1:30   every 4:00   ~5 per 20 min
    balanced  first 2:00   every 5:00   ~4 per 20 min
    viewer    first 3:00   every 8:00   ~2 per 20 min

With an .srt/.vtt each ad is moved to the longest pause within about 45 seconds of its slot, with a
bonus for a chapter start, so it lands between sentences. Without a transcript the slots are exact
and you should nudge each to the nearest pause by hand. Because of the snapping, neighbouring ads
can end up a little closer than --gap (never closer than gap minus 90 seconds).

More ads earn more per view and usually cost watch time; YouTube may also leave some slots empty
(Studio flags slots unlikely to show ads). Check retention after a week and back off if it drops.
Tested: evenly spaced slots entered without a transcript were ALL flagged by Studio as unlikely to
show ads. Pass --srt so ads land on real pauses, and re-check the warnings after saving.
YouTube has required about 8 minutes of length for mid-roll ads; check Studio near that line.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yt-edit"))


def to_sec(s):
    parts = [float(p) for p in str(s).strip().split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def mmss(t):
    t = int(round(t)); h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def arg(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def pauses(path):
    from deadair import load  # same SRT/VTT parser the other skills use
    cues = load(path)
    return [(cues[i][0] - cues[i - 1][1], cues[i - 1][1], cues[i][0]) for i in range(1, len(cues))]


MODES = {"earn": (90, 240), "balanced": (120, 300), "viewer": (180, 480)}
SNAP = 45  # seconds either side of an ideal slot to look for a pause
TAIL = 60  # keep the last minute ad-free


def pick(dur, first, gap, maximum, gaps, chapters):
    last = dur - TAIL
    if last < first:
        return []
    want = max(1, min(maximum, int((last - first) // gap) + 1))
    step = gap
    chosen = []
    for i in range(want):
        target = first + step * i
        best = target
        if gaps:
            options = []
            for g, a, b in gaps:
                mid = (a + b) / 2
                if abs(mid - target) <= SNAP and first <= mid <= last and g >= 0.6:
                    options.append((g + (3 if any(abs(mid - c) <= 15 for c in chapters) else 0), -abs(mid - target), mid))
            if options:
                best = max(options)[2]
        if not chosen or best - chosen[-1] >= gap - 2 * SNAP:
            chosen.append(best)
    return chosen


def main():
    a = sys.argv[1:]
    if "--duration" not in a:
        print(__doc__)
        sys.exit(1)
    mode = arg(a, "--mode", "earn")
    if mode not in MODES:
        print(f"--mode must be one of: {', '.join(MODES)}")
        sys.exit(1)
    dur = to_sec(arg(a, "--duration"))
    first = to_sec(arg(a, "--first", MODES[mode][0]))
    gap = to_sec(arg(a, "--gap", MODES[mode][1]))
    maximum = int(arg(a, "--max", "30"))
    chapters = [to_sec(c) for c in arg(a, "--chapters", "").split(",") if c.strip()]
    srt = arg(a, "--srt")
    if srt and not os.path.exists(srt):
        print(f"no such file: {srt}")
        sys.exit(1)
    if dur < 480:
        print("note: under 8 minutes, Studio may not offer mid-roll placement for this video.\n")
    points = pick(dur, first, gap, maximum, pauses(srt) if srt else [], chapters)
    if not points:
        print("video is too short for the spacing you asked for; use pre/post-roll only or lower --first/--gap")
        return
    print("mid-roll breakpoints:")
    for p in points:
        print(f"  {mmss(p):>7}   Studio box: {int(p) // 60:02d}:{int(p) % 60:02d}:00")
    print(f"\n{len(points)} ads over {mmss(dur)}")
    if not srt:
        print("no transcript given: these are evenly spaced. Move each to the nearest pause before saving.")


if __name__ == "__main__":
    main()
