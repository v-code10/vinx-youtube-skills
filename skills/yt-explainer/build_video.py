#!/usr/bin/env python3
"""build_video.py - turn a storyboard into a narrated teaching video (MP4 + SRT + description).

    python3 build_video.py storyboard.json out/binary-search --ffmpeg /path/to/ffmpeg
    python3 build_video.py storyboard.json out/x --voice "Microsoft Zira Desktop" --rate -1
    python3 build_video.py storyboard.json out/x --voice models/en_US-ryan-high.onnx   # Piper neural voice (offline)
    python3 build_video.py short.json out/short --format shorts         # 1080x1920 vertical, for Shorts
    python3 build_video.py short.json out/short --format shorts --audio-dir my-recordings/   # your own voice

Needs ffmpeg (--ffmpeg, the FFMPEG environment variable, or PATH) and a text-to-speech engine. Voices are
generated OFFLINE: Windows SAPI, macOS `say`, Linux `espeak-ng`. Standard library only. Run
lint_storyboard.py first: it checks the teaching structure and the originality fields.

Writes <out>.mp4, <out>.srt and <out>.description.txt (summary, chapters, synthetic-voice disclosure,
sources, hashtags).

Scene kinds ("kind", default "card"). Every scene has `narration`; the rest depends on the kind:
  card     headline, sub, optional code (list of lines) and highlight [{"line":0,"at":0.2},...]
  steps    headline, items [str,...]            items appear one by one while the narration runs
  stack    headline, frames [str,...], unwind   a call stack that grows, then (unwind=true) pops
  array    headline, values [...], steps [{"low":0,"high":9,"mid":4,"note":"..."}]   binary-search style
  compare  headline, left {"title","items"}, right {"title","items"}                  wrong vs right
Common optional fields: sub (small tag), bg, accent (hex), hold (seconds of silence for the viewer to think),
role (hook/story/concept/demo/mistake/recap/cta, used by the linter), chapter (title used in the description).
"""
import json, os, shutil, subprocess, sys, tempfile, textwrap

W, H = 1280, 720
CAP_RESERVE = 190  # bottom area kept for captions


def arg(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def find_ffmpeg(explicit):
    for cand in (explicit, os.environ.get("FFMPEG"), shutil.which("ffmpeg")):
        if cand and (os.path.exists(cand) or shutil.which(cand)):
            return cand
    sys.exit("ffmpeg not found: install it or pass --ffmpeg C:\\path\\to\\ffmpeg.exe")


def ff_path(p):
    return p.replace("\\", "/").replace(":", "\\:")


def find_piper(model):
    here = os.path.dirname(os.path.abspath(model))
    for cand in (os.environ.get("PIPER"), shutil.which("piper"), os.path.join(here, "piper", "piper.exe"),
                 os.path.join(here, "piper.exe"), os.path.join(here, "piper", "piper")):
        if cand and os.path.exists(cand):
            return cand
    sys.exit("piper not found: set PIPER or put the piper folder next to the .onnx model")


def synth(text, out_wav, voice, rate, tmp):
    txt = os.path.join(tmp, "tts.txt")
    with open(txt, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    if voice and voice.lower().endswith(".onnx"):
        scale = 1.0 / (1.0 + 0.1 * float(rate))
        with open(txt, "rb") as fh:
            subprocess.run([find_piper(voice), "--model", voice, "--length_scale", f"{scale:.2f}",
                            "--output_file", out_wav], stdin=fh, check=True, capture_output=True)
        return
    if sys.platform.startswith("win"):
        ps = ("Add-Type -AssemblyName System.Speech;"
              "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
              + (f"$s.SelectVoice('{voice}');" if voice else "")
              + f"$s.Rate={int(rate)};$s.SetOutputToWaveFile('{out_wav}');"
              f"$s.Speak([IO.File]::ReadAllText('{txt}',[Text.Encoding]::UTF8));$s.Dispose()")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    elif sys.platform == "darwin":
        aiff = out_wav + ".aiff"
        subprocess.run(["say", "-o", aiff, "-f", txt] + (["-v", voice] if voice else []), check=True)
        os.replace(aiff, out_wav)
    else:
        subprocess.run(["espeak-ng", "-f", txt, "-w", out_wav] + (["-v", voice] if voice else []), check=True)


def duration(ffmpeg, wav):
    probe = shutil.which("ffprobe") or os.path.join(os.path.dirname(ffmpeg), "ffprobe.exe")
    out = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


class Painter:
    """Builds ffmpeg drawtext/drawbox filters for one scene. Everything is timed against the scene clock."""

    def __init__(self, tmp, idx, font, mono, accent, dur):
        self.tmp, self.idx, self.font, self.mono, self.accent, self.dur = tmp, idx, font, mono, accent, dur
        self.f, self.n = [], 0

    def _file(self, text):
        self.n += 1
        p = os.path.join(self.tmp, f"s{self.idx}_{self.n}.txt")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return ff_path(p)

    def text(self, text, x, y, size, color="white", at=0.0, until=None, mono=False, box=None):
        if until is None:
            alpha = f"min(1,max(0,(t-{at:.2f})/0.3))"
        else:
            alpha = f"if(between(t,{at:.2f},{until:.2f}),min(1,(t-{at:.2f})/0.3),0)"
        font = self.mono if mono else self.font
        extra = f":box=1:boxcolor={box}:boxborderw=12" if box else ""
        self.f.append(f"drawtext=fontfile='{font}':textfile='{self._file(text)}':fontcolor={color}:fontsize={size}:"
                      f"x={x}:y={y}:alpha='{alpha}'{extra}")

    def rect(self, x, y, w, h, color, at=0.0, until=None, opacity=1.0):
        until = self.dur + 1 if until is None else until
        self.f.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color={color}@{opacity}:t=fill:"
                      f"enable='between(t,{at:.2f},{until:.2f})'")

    def caption(self, narration):
        cap = "\n".join(textwrap.wrap(narration, 68))
        self.f.append(f"drawtext=fontfile='{self.font}':textfile='{self._file(cap)}':fontcolor=white:fontsize=30:"
                      f"line_spacing=6:x=(w-text_w)/2:y=h-text_h-40:box=1:boxcolor=black@0.55:boxborderw=14")

    def progress(self):
        self.f.append(f"drawbox=x=0:y=ih-10:w='iw*t/{self.dur:.3f}':h=10:color={self.accent}:t=fill")

    def filters(self):
        return ",".join(self.f)


def reveal_times(n, dur, start=0.9, share=0.7):
    if n <= 0:
        return []
    span = max(1.0, dur * share - start)
    gap = span / max(n, 1)
    return [start + i * gap for i in range(n)]


def build_scene(sc, idx, dur, tmp, font, mono):
    accent = "0x" + sc.get("accent", "#ffd400").lstrip("#")
    p = Painter(tmp, idx, font, mono, accent, dur)
    kind = sc.get("kind", "card")
    big = kind == "card" and not sc.get("code")
    head = sc.get("headline", "")
    if sc.get("sub"):
        p.text(sc["sub"].upper(), 70, 40, 34, accent, at=0.0)
    if head:
        wrapped = "\n".join(textwrap.wrap(head.upper(), 18 if big else 30))
        p.text(wrapped, 70, 90 if big else 82, 92 if big else 58, "white", at=0.0)

    if kind == "card":
        code = sc.get("code")
        if code:
            size = max(22, min(36, int(250 / (len(code) * 1.5))))
            pitch = int(size * 1.5)
            top = 210
            p.rect(50, top - 14, 1180, pitch * len(code) + 28, "0x000000", opacity=0.35)
            ts = reveal_times(len(code), dur, 0.6, 0.35)
            for i, line in enumerate(code):
                p.text(line, 70, top + i * pitch, size, accent, at=ts[i], mono=True)
            marks = sc.get("highlight") or []
            for j, m in enumerate(marks):
                a = float(m.get("at", 0)) * dur
                b = float(marks[j + 1].get("at", 1)) * dur if j + 1 < len(marks) else dur
                p.rect(50, top + m["line"] * pitch - 8, 1180, pitch, accent, at=a, until=b, opacity=0.28)
    elif kind == "steps":
        items = sc.get("items", [])
        ts = reveal_times(len(items), dur)
        for i, it in enumerate(items):
            p.rect(70, 196 + i * 74, 12, 50, accent, at=ts[i])
            p.text(it, 100, 196 + i * 74, 44, "white", at=ts[i])
    elif kind == "stack":
        frames = sc.get("frames", [])
        ts = reveal_times(len(frames), dur, 0.9, 0.5)
        pop0 = dur * 0.62
        gap = max(0.5, (dur * 0.30) / max(len(frames), 1))
        base, bh = 520, 62
        for i, fr in enumerate(frames):
            y = base - (i + 1) * (bh + 8)
            out = (pop0 + (len(frames) - 1 - i) * gap) if sc.get("unwind") else dur + 1
            shade = "0x1d4ed8" if i % 2 == 0 else "0x2563eb"
            p.rect(380, y, 520, bh, shade, at=ts[i], until=out, opacity=0.95)
            p.text(fr, 410, y + 12, 36, "white", at=ts[i], until=out, mono=True)
        p.rect(340, base, 600, 6, accent, at=0.5)
        if sc.get("unwind") and sc.get("note"):
            p.text(sc["note"], 380, base + 16, 30, accent, at=pop0)
    elif kind == "array":
        vals = sc.get("values", [])
        steps = sc.get("steps", [])
        n = len(vals)
        bw, gapx = 100, 10
        x0 = (W - (n * bw + (n - 1) * gapx)) // 2
        y0 = 270
        for i, v in enumerate(vals):
            p.rect(x0 + i * (bw + gapx), y0, bw, 90, "0x334155", at=0.2)
            p.text(str(v), x0 + i * (bw + gapx) + bw // 2 - 14 * len(str(v)), y0 + 24, 42, "white", at=0.2)
        ts = reveal_times(len(steps), dur, 1.0, 0.85)
        for k, st in enumerate(steps):
            a = ts[k]
            b = ts[k + 1] if k + 1 < len(steps) else dur
            lo, hi, mid = st["low"], st["high"], st["mid"]
            for i in range(n):
                x = x0 + i * (bw + gapx)
                if i < lo or i > hi:
                    p.rect(x, y0, bw, 90, "0x000000", at=a, until=b, opacity=0.65)
            xm = x0 + mid * (bw + gapx)
            p.rect(xm - 4, y0 - 4, bw + 8, 98, accent, at=a, until=b, opacity=0.9)
            p.text(str(vals[mid]), xm + bw // 2 - 14 * len(str(vals[mid])), y0 + 24, 42, "0x111111", at=a, until=b)
            for label, pos in (("LOW", lo), ("MID", mid), ("HIGH", hi)):
                p.text(label, x0 + pos * (bw + gapx) + 12, y0 + 104 + (30 if label == "MID" else 0), 26, accent, at=a, until=b)
            if st.get("note"):
                p.text(st["note"], 70, 440, 38, "white", at=a, until=b)
    elif kind == "compare":
        for side, color, x in (("left", "0xff5d73", 70), ("right", "0x5eead4", 670)):
            col = sc.get(side, {})
            p.text(col.get("title", "").upper(), x, 190, 40, color, at=0.5)
            items = col.get("items", [])
            ts = reveal_times(len(items), dur, 1.0 if side == "left" else 1.4, 0.7)
            for i, it in enumerate(items):
                p.text("\n".join(textwrap.wrap(it, 26)), x, 255 + i * 90, 32, "white", at=ts[i])
    p.caption(sc["narration"])
    p.progress()
    return p.filters()


class PortraitPainter(Painter):
    """Same primitives, laid out for 1080x1920. Captions sit above YouTube's bottom UI, the progress strip on top."""

    def caption(self, narration):
        cap = "\n".join(textwrap.wrap(narration, 28))
        self.f.append(f"drawtext=fontfile='{self.font}':textfile='{self._file(cap)}':fontcolor=white:fontsize=48:"
                      f"line_spacing=10:x=(w-text_w)/2:y=1330:box=1:boxcolor=black@0.6:boxborderw=18")

    def progress(self):
        self.f.append(f"drawbox=x=0:y=0:w='iw*t/{self.dur:.3f}':h=12:color={self.accent}:t=fill")


def lines_of(text, width):
    return "\n".join(textwrap.wrap(text, width)) if text else ""


def build_scene_portrait(sc, idx, dur, tmp, font, mono):
    """9:16 layout. Safe area: y 220 to 1300 for content, captions from 1330, nothing below 1650."""
    accent = "0x" + sc.get("accent", "#ffd400").lstrip("#")
    p = PortraitPainter(tmp, idx, font, mono, accent, dur)
    kind = sc.get("kind", "card")
    y = 230
    if sc.get("sub"):
        p.text(sc["sub"].upper(), 60, y, 44, accent)
        y += 78
    head = sc.get("headline", "")
    big = kind == "card" and not sc.get("code")
    size = 118 if big else 90
    wrapped = lines_of(head.upper(), 9 if big else 12)
    if head:
        p.text(wrapped, 60, y, size, "white")
        y += int(size * 1.2) * (wrapped.count("\n") + 1) + 36

    if kind == "card" and sc.get("code"):
        code = sc["code"]
        pitch = 62
        p.rect(36, y - 14, 1008, pitch * len(code) + 28, "0x000000", opacity=0.4)
        ts = reveal_times(len(code), dur, 0.6, 0.35)
        for i, line in enumerate(code):
            p.text(line, 56, y + i * pitch, 40, accent, at=ts[i], mono=True)
        for j, m in enumerate(sc.get("highlight") or []):
            marks = sc["highlight"]
            a = float(m.get("at", 0)) * dur
            b = float(marks[j + 1].get("at", 1)) * dur if j + 1 < len(marks) else dur
            p.rect(36, y + m["line"] * pitch - 8, 1008, pitch, accent, at=a, until=b, opacity=0.3)
    elif kind == "steps":
        items = sc.get("items", [])
        ts = reveal_times(len(items), dur)
        for i, it in enumerate(items):
            txt = lines_of(it, 17)
            n = txt.count("\n") + 1
            p.rect(60, y, 16, n * 78, accent, at=ts[i])
            p.text(txt, 100, y, 64, "white", at=ts[i])
            y += n * 78 + 44
    elif kind == "compare":
        for side, color in (("left", "0xff5d73"), ("right", "0x5eead4")):
            col = sc.get(side, {})
            t0 = 0.5 if side == "left" else dur * 0.45
            p.text(col.get("title", "").upper(), 60, y, 58, color, at=t0)
            y += 82
            items = col.get("items", [])
            ts = reveal_times(len(items), dur * (0.4 if side == "left" else 1.0), t0 + 0.4, 0.8)
            for i, it in enumerate(items):
                txt = lines_of(it, 28)
                n = txt.count("\n") + 1
                p.text(txt, 60, y, 54, "white", at=ts[i])
                y += n * 66 + 26
            y += 36
    elif kind == "stack":
        frames = sc.get("frames", [])
        ts = reveal_times(len(frames), dur, 0.9, 0.5)
        pop0 = dur * 0.62
        gap = max(0.5, (dur * 0.30) / max(len(frames), 1))
        base, bh = 1240, 92
        for i, fr in enumerate(frames):
            by = base - (i + 1) * (bh + 12)
            out = (pop0 + (len(frames) - 1 - i) * gap) if sc.get("unwind") else dur + 1
            p.rect(130, by, 820, bh, "0x1d4ed8" if i % 2 == 0 else "0x2563eb", at=ts[i], until=out, opacity=0.95)
            p.text(fr, 160, by + 24, 40, "white", at=ts[i], until=out, mono=True)
        p.rect(90, base, 900, 8, accent, at=0.5)
    elif kind == "array":
        vals, steps = sc.get("values", []), sc.get("steps", [])
        n = len(vals)
        gapx = 8
        bw = (1000 - (n - 1) * gapx) // n
        x0, y0 = 40, y + 50
        fs = 48 if bw >= 80 else 36
        for i, v in enumerate(vals):
            p.rect(x0 + i * (bw + gapx), y0, bw, 130, "0x334155", at=0.2)
            p.text(str(v), x0 + i * (bw + gapx) + bw // 2 - (fs // 4) * len(str(v)) - 2, y0 + 38, fs, "white", at=0.2)
        ts = reveal_times(len(steps), dur, 1.0, 0.85)
        for k, st in enumerate(steps):
            a = ts[k]
            b = ts[k + 1] if k + 1 < len(steps) else dur
            lo, hi, mid = st["low"], st["high"], st["mid"]
            for i in range(n):
                if i < lo or i > hi:
                    p.rect(x0 + i * (bw + gapx), y0, bw, 130, "0x000000", at=a, until=b, opacity=0.65)
            xm = x0 + mid * (bw + gapx)
            p.rect(xm - 4, y0 - 4, bw + 8, 138, accent, at=a, until=b, opacity=0.9)
            p.text(str(vals[mid]), xm + bw // 2 - (fs // 4) * len(str(vals[mid])) - 2, y0 + 38, fs, "0x111111", at=a, until=b)
            for label, pos in (("LOW", lo), ("MID", mid), ("HIGH", hi)):
                p.text(label, x0 + pos * (bw + gapx) + 4, y0 + 148 + (34 if label == "MID" else 0), 28, accent, at=a, until=b)
            if st.get("note"):
                p.text(lines_of(st["note"], 20), 60, y0 + 290, 64, "white", at=a, until=b)
    p.caption(sc.get("caption") or sc["narration"])
    p.progress()
    return p.filters()


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def stamp(t):
    t = int(t)
    return f"{t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def description(sb, starts, own_voice=False, shorts=False):
    lines = [sb.get("summary", sb.get("title", "")), ""]
    chaps = [(starts[i], s["chapter"]) for i, s in enumerate(sb["scenes"]) if s.get("chapter")]
    ok = len(chaps) >= 3 and chaps[0][0] == 0 and all(b[0] - a[0] >= 10 for a, b in zip(chaps, chaps[1:]))
    if ok and not shorts:
        lines += [f"{stamp(t)} {title}" for t, title in chaps] + [""]
    elif not shorts:
        lines += ["(chapters skipped: YouTube needs a chapter at 0:00, at least three, each 10s or longer)", ""]
    if own_voice:
        lines.append("Voice: recorded by the creator. " + sb.get("disclosure_extra", ""))
    else:
        lines.append("Narration is a synthetic (text-to-speech) voice. " + sb.get("disclosure_extra", ""))
    lines.append(f"Script, structure and visuals by {sb.get('author', 'the channel')}.")
    if sb.get("sources"):
        lines += ["", "Sources:"] + [f"- {s}" for s in sb["sources"]]
    if sb.get("hashtags"):
        lines += ["", " ".join(sb["hashtags"])]
    return "\n".join(lines).strip() + "\n"


def find_audio(folder, idx):
    for ext in ("wav", "mp3", "m4a", "aac", "ogg", "flac"):
        p = os.path.join(folder, f"scene{idx + 1:02d}.{ext}")
        if os.path.exists(p):
            return p
    return None


def main():
    global W, H
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        sys.exit(1)
    sb = json.load(open(a[0], encoding="utf-8"))
    out = a[1]
    shorts = arg(a, "--format", "landscape") == "shorts"
    if shorts:
        W, H = 1080, 1920
    audio_dir = arg(a, "--audio-dir")
    builder = build_scene_portrait if shorts else build_scene
    ffmpeg = find_ffmpeg(arg(a, "--ffmpeg"))
    voice = arg(a, "--voice", sb.get("voice"))
    rate = arg(a, "--rate", sb.get("rate", 0))
    fonts = os.environ.get("WINDIR", "C:\\Windows") + "\\Fonts\\"
    font = ff_path(arg(a, "--font", fonts + "arialbd.ttf" if sys.platform.startswith("win") else "/Library/Fonts/Arial Bold.ttf"))
    mono = ff_path(arg(a, "--mono", fonts + "consola.ttf" if sys.platform.startswith("win") else "/Library/Fonts/Courier New.ttf"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="ytexp_")
    clips, srt, starts, t0, own, prompt = [], [], [], 0.0, 0, []
    try:
        for i, sc in enumerate(sb["scenes"]):
            wav = os.path.join(tmp, f"s{i}.wav")
            mine = find_audio(audio_dir, i) if audio_dir else None
            if mine:
                subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", mine, "-ar", "44100", "-ac", "1", wav], check=True)
                own += 1
            else:
                synth(sc["narration"], wav, voice, rate, tmp)
            hold = float(sc.get("hold", 0))
            dur = duration(ffmpeg, wav) + 0.35 + hold
            clip = os.path.join(tmp, f"s{i}.mp4")
            bg = sc.get("bg", "#0b1020").lstrip("#")
            vf = builder(sc, i, dur, tmp, font, mono)
            subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=0x{bg}:s={W}x{H}:r=30:d={dur:.3f}",
                            "-i", wav, "-vf", vf, "-af", f"apad=pad_dur={0.35 + hold}", "-t", f"{dur:.3f}", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", "-ac", "2", clip], check=True)
            clips.append(clip)
            starts.append(t0)
            shown = sc.get("caption") or sc["narration"]
            srt.append(f"{i + 1}\n{srt_time(t0)} --> {srt_time(t0 + dur - hold)}\n{shown}\n")
            prompt.append(f"scene{i + 1:02d}  (about {dur:.0f}s)\n{sc['narration']}\n")
            t0 += dur
            print(f"scene {i + 1}/{len(sb['scenes'])} [{sc.get('kind', 'card')}]: {dur:.1f}s")
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w", encoding="utf-8") as fh:
            fh.write("".join(f"file '{c.replace(chr(92), '/')}'\n" for c in clips))
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out + ".mp4"], check=True)
        with open(out + ".srt", "w", encoding="utf-8") as fh:
            fh.write("\n".join(srt))
        with open(out + ".description.txt", "w", encoding="utf-8") as fh:
            fh.write(description(sb, starts, own_voice=own == len(sb["scenes"]), shorts=shorts))
        with open(out + ".teleprompter.txt", "w", encoding="utf-8") as fh:
            fh.write("Record each scene as scene01.wav, scene02.wav ... in one folder, then rebuild with --audio-dir that folder.\n\n" + "\n".join(prompt))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    note = ""
    if shorts and t0 > 59:
        note = f"  WARNING: {t0:.0f}s is over 60 seconds, so YouTube will not treat it as a Short. Cut text."
    print(f"done: {out}.mp4 ({t0:.0f}s, {W}x{H}), .srt, .description.txt, .teleprompter.txt{note}")


if __name__ == "__main__":
    main()
