#!/usr/bin/env python3
"""lint_storyboard.py - check a storyboard for teaching structure, originality and repetition before building.

    python3 lint_storyboard.py storyboard.json
    python3 lint_storyboard.py storyboard.json --history my-earlier-storyboards/
    python3 lint_storyboard.py short.json --shorts          # vertical Short: must finish under 60 seconds
    python3 lint_storyboard.py short.json --shorts --wps 3.0   # faster voice (Piper English measured about 3)

Exit code 2 if a required item is missing, 0 otherwise (warnings do not fail).

What it checks, and why:
  * roles: a video that teaches needs a hook, a concept, a demonstration, a common mistake and a recap.
    Tag each scene with "role" (hook, story, concept, demo, mistake, recap, cta).
  * originality fields: "original_value" (what a viewer gets here that they would not get from the
    obvious copy of this topic), "sources" (where facts came from) and "author". YouTube's policies target
    mass-produced, repetitive or low-effort content, so these are the things that make a video yours.
  * pace and clarity: very long sentences, very long scenes, wall-of-text headlines.
  * repetition (--history): high word overlap or an identical scene structure with earlier videos is the
    template-reuse pattern to avoid.
It cannot judge whether the content is correct or good. A person has to read it.
"""
import glob, json, os, re, sys

REQUIRED_ROLES = ["hook", "concept", "demo", "mistake", "recap"]
WPS = 2.1  # spoken words per second measured on a real build (system voice, includes scene padding)


def words(text):
    return re.findall(r"[a-z']+", text.lower())


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    sb = json.load(open(a[0], encoding="utf-8"))
    scenes = sb.get("scenes", [])
    shorts = "--shorts" in a
    wps = float(a[a.index("--wps") + 1]) if "--wps" in a else WPS
    fail, warn = [], []

    roles = [s.get("role") for s in scenes]
    for r in (["hook", "demo", "recap"] if shorts else REQUIRED_ROLES):
        if r not in roles:
            fail.append(f"no scene with role '{r}'")
    if roles and roles[0] != "hook":
        warn.append("the first scene is not the hook; open with the problem, not the definition")
    if roles and roles[-1] not in ("recap", "cta"):
        warn.append("end with a recap or one ask")

    for field in ("original_value", "author"):
        if not str(sb.get(field, "")).strip():
            fail.append(f"missing '{field}' (what is original about this video / who made it)")
    if not sb.get("sources"):
        fail.append("missing 'sources' (list where the facts came from, even if it is 'own experience: ...')")

    total = 0.0
    for i, s in enumerate(scenes, 1):
        n = len(words(s.get("narration", "")))
        total += n / wps + 0.35 + float(s.get("hold", 0))
        for sent in re.split(r"[.!?]", s.get("narration", "")):
            if len(words(sent)) > 28:
                warn.append(f"scene {i}: a sentence of {len(words(sent))} words; split it")
        if n > (32 if shorts else 60):
            warn.append(f"scene {i}: {n} words is long for one idea; split the scene")
        if len(s.get("headline", "")) > (24 if shorts else 36):
            warn.append(f"scene {i}: headline over {24 if shorts else 36} characters will wrap badly")
        if shorts:
            for line in s.get("code", []) or []:
                if len(line) > 40:
                    warn.append(f"scene {i}: code line over 40 characters will not fit a vertical frame: {line[:30]}...")
            for k in ("items",):
                for it in s.get(k, []) or []:
                    if len(it) > 44:
                        warn.append(f"scene {i}: list item over 44 characters wraps to 3 lines: {it[:30]}...")
        if not s.get("narration", "").strip():
            fail.append(f"scene {i}: empty narration")
    if shorts:
        if total > 59:
            fail.append(f"about {total:.0f}s: a Short must be under 60 seconds; cut words or scenes")
        elif total > 52:
            warn.append(f"about {total:.0f}s: close to the limit; real voice pace can run longer than this estimate")
        if not 4 <= len(scenes) <= 8:
            warn.append(f"{len(scenes)} scenes: 4 to 8 keeps a Short moving without being a blur")
        if scenes and len(words(scenes[0].get("narration", ""))) > 26:
            warn.append("the hook is long; the first 3 seconds decide whether anyone stays")
    else:
        if total < 45:
            warn.append(f"about {total:.0f}s: very short; is the idea fully taught?")
        if total > 240:
            warn.append(f"about {total:.0f}s: long for this format; consider splitting into two videos")

    if "--history" in a:
        folder = a[a.index("--history") + 1]
        mine = words(" ".join(s.get("narration", "") for s in scenes))
        for path in glob.glob(os.path.join(folder, "*.json")):
            if os.path.abspath(path) == os.path.abspath(a[0]):
                continue
            try:
                other = json.load(open(path, encoding="utf-8"))
            except ValueError:
                continue
            theirs = words(" ".join(s.get("narration", "") for s in other.get("scenes", [])))
            sim = jaccard(mine, theirs)
            same_shape = [s.get("role") for s in other.get("scenes", [])] == roles and len(roles) > 0
            if sim > 0.55:
                warn.append(f"{os.path.basename(path)}: {sim:.0%} word overlap; this reads like a re-run")
            elif same_shape and sim > 0.35:
                warn.append(f"{os.path.basename(path)}: identical scene structure and {sim:.0%} overlap; vary the structure")

    print(f"about {total:.0f}s, {len(scenes)} scenes")
    for m in fail:
        print("FAIL ", m)
    for m in warn:
        print("warn ", m)
    if not fail and not warn:
        print("ok")
    print("\nA person still has to read and listen to the result: this checks structure, not truth.")
    sys.exit(2 if fail else 0)


if __name__ == "__main__":
    main()
