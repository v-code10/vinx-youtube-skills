---
name: yt-short-explainer
description: Make a vertical (1080x1920, 9:16) YouTube Short under 60 seconds that explains one DSA or system design idea in plain, friendly English with a natural-sounding offline voice. Use when the user asks for Shorts, quick interview-concept clips, or a short explainer on a DSA or system design topic. Builds on yt-explainer's builder and linter.
---

# yt-short-explainer

One idea per Short, English only. A storyboard (JSON) goes in; an `.mp4`, `.srt`, description and
teleprompter file come out. Scripts live in `../yt-explainer/`.

## Voice setup (once): Piper neural voice, offline

The built-in Windows voices (David, Zira) sound robotic. Piper gives a much more natural English voice
and runs offline with no Python packages:

1. Download the Piper Windows release (`piper_windows_amd64.zip`) from the rhasspy/piper GitHub releases and unzip it into a folder, so you have `<folder>/piper/piper.exe`.
2. Download a voice, both files, from the rhasspy/piper-voices page on Hugging Face, for example
   `en_US-ryan-high.onnx` and `en_US-ryan-high.onnx.json`, into the same `<folder>`.
3. Pass the model path with `--voice`. The builder finds `piper.exe` next to it (or use the `PIPER` environment variable).

Check each voice's licence and model card before using it commercially. Other English voices there
(for example `en_US-lessac-high`, `en_GB-alan-medium`) can be compared by ear.

## Run it

```
python ../yt-explainer/lint_storyboard.py my-short.json --shorts --wps 3.0
python ../yt-explainer/build_video.py my-short.json out/my-short --format shorts --voice C:\voices\en_US-ryan-high.onnx
```

- `--shorts` fails above 59 s. `--wps` is the voice's words per second: about 2.1 for the Windows voices,
  about 3.0 for Piper. Trust the build's printed length over the estimate.
- Examples to copy: `example-binary-search.json` (DSA, about 40 s with Piper) and `example-cache.json`
  (system design, about 41 s). Aim for 35 to 55 s.
- Scene kinds: `card`, `steps`, `array`, `compare`, `stack`. Roles required in Shorts mode:
  `hook`, `demo`, `recap`. Also required: `author`, `original_value`, `sources`.

## Script style

- Plain spoken English, short sentences (8 to 12 words), no jargon without a one-line explanation.
- Hook in the first 3 seconds: a challenge or a problem, not a definition.
- One everyday example per Short. Humour only if it helps remember the point.
- Say the term once (cache hit, stale data) and explain it in the same breath.
- About 5 scenes: hook, 2 to 3 explanation scenes, recap with a follow line.
- Keep on-screen text to a few words per line; the caption box shows the narration.
- Write numbers the way you want them spoken ("twenty-three", "double slash").

## Before publishing

- A person must watch the full Short and check every fact and how the voice pronounces terms.
- Keep it vertical and under 60 seconds; the builder adds `#shorts` to the description.
- Disclose the synthetic voice (the builder writes this into the description).
- YouTube's policies on repetitive or mass-produced content and on altered or synthetic content apply.
  Check the current Help pages before relying on monetization. Each Short needs its own idea, script
  and example; do not swap only the numbers in a template.
- Your own recorded voice (`--audio-dir`, using the `.teleprompter.txt`) is the most clearly original option.
- Nothing here guarantees views or monetization.
