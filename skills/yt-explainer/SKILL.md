---
name: yt-explainer
description: >-
  Plan and build a short (1 to 3 minute) narrated teaching video on one concept, with a story, real
  visuals (step-by-step array, call stack, code highlight, wrong-versus-right), a think-for-yourself
  pause, an offline synthetic voice, captions, chapters and a compliant description. Use for "make a
  short video explaining X", "teach this concept simply and funnily", "turn this script into a video".
---

# yt-explainer

A storyboard goes in; an MP4, an SRT and a ready description come out. The voice is generated on the
machine from the system's text-to-speech (Windows SAPI, macOS `say`, Linux `espeak-ng`). Nothing is
sent to a cloud service.

Files: `build_video.py` (builds), `lint_storyboard.py` (checks structure, originality, repetition),
`example-binary-search.json` (a complete, linted example you can copy).

## What makes it teach, not just narrate

Build the video in this order; the linter checks the roles are present.

1. **hook**: a problem or a surprise, not a definition. ("Ten guesses to find any number from 1 to
   1000. Can you always win?")
2. **story**: the slow or naive way against the smart way, or a small situation the viewer recognises.
3. **concept**: the whole idea in three or four short steps.
4. **demo**: show it working one step at a time (the `array` visual moves low, mid and high; `stack`
   grows and unwinds a call stack; `card` with `code` highlights the line being explained).
5. **mistake**: the one or two errors beginners really make, as wrong versus right.
6. **think**: a scene with `hold` seconds of silence and a question, so the viewer predicts before
   you answer.
7. **recap** (and one ask): four lines to keep.

Writing rules: one idea per scene, 1 to 3 short sentences; accuracy before jokes; one joke per scene
at most, tied to the idea; never state something false for a laugh. Spell odd words phonetically in
`narration` so the voice says them right.

## Scene kinds

`card` (headline, optional `code` plus `highlight`), `steps` (`items` reveal one by one), `stack`
(`frames`, `unwind`), `array` (`values` and `steps` of low/high/mid with a `note`), `compare`
(`left` and `right` columns). Common: `sub`, `bg`, `accent`, `hold`, `role`, `chapter`. See the
docstring at the top of `build_video.py` for every field.

## Steps

1. Write the storyboard (copy `example-binary-search.json`). Fill `author`, `original_value` and
   `sources`: these are about what is yours, not decoration.
2. Lint it. Fix every FAIL; read every warn:

   ```
   python3 lint_storyboard.py storyboard.json --history folder-of-earlier-storyboards/
   ```

3. Build it:

   ```
   python3 build_video.py storyboard.json out/my-video --ffmpeg /path/to/ffmpeg
   ```

4. **A person checks it.** Watch and listen to the whole thing: pronunciation, pace, whether every
   claim is true, whether the jokes land, any text that wraps badly. Extract a few frames with
   `ffmpeg -ss 60 -i out/my-video.mp4 -frames:v 1 frame.png` if you want to inspect layout.
5. Package with `/yt-package` and `/yt-seo`. The generated `.description.txt` already has the summary,
   valid chapters, the synthetic-voice disclosure and the sources; add links and tags.
6. Upload the MP4, attach the `.srt`, answer Studio's altered or synthetic content question honestly.

## Following YouTube's rules (and what that does and does not buy you)

This is my understanding; read YouTube's current Help Center pages before publishing, because the
policies change:

- **Use of AI is allowed; mass-produced or repetitive content is not monetised.** YouTube's Partner
  Programme policies target "inauthentic" content: templated videos made in bulk with little
  original input. What protects a channel is real original value per video: your own explanation,
  structure and examples. That is why the linter requires `original_value`, `sources` and
  `author`, and why `--history` warns when a new storyboard reuses an old one's words or shape.
  Do not publish a stream of near-identical videos from this tool.
- **Disclose synthetic content.** The description states the narration is synthetic. Answer the
  "altered or synthetic content" question in Studio truthfully. A plainly robotic system voice is not
  a realistic person, but do not rely on my reading of that; check the question's wording.
- **Do not mislead.** No fake claims, fake testimonials or invented statistics. The linter cannot
  check truth: you must.
- **Copyright.** Visuals are generated text and shapes. If you add music or footage, use only what you
  are licensed to use.
- **Voice licence.** The built-in voices come under their maker's terms. I have not verified whether
  they permit commercial use in published videos; check before monetising, or use a voice whose
  licence you have read.
- **Monetisation also needs** an account in the Partner Programme and its thresholds. No tool can
  guarantee a video earns anything.

## Limits

The picture is clean text and shapes, not animation, and the voice is a system voice. For a warmer
result, record your own narration over the same storyboard and replace the audio in an editor. This was
tested on Windows with the built-in voices and a portable ffmpeg; macOS and Linux paths are untested.
