---
name: yt-boost
description: >-
  Take ONE video, new or underperforming, and fix everything that can be fixed from Studio: title,
  description, tags, chapters, monetization and mid-roll check, thumbnail, and the promotion steps
  that help it rank. Use when the creator names a single video to "fix", "boost", "rank", "make
  viral", or has just uploaded a new video and wants it set up properly.
---

# yt-boost

One video at a time. It runs the other skills in a fixed order, applies the result through Studio,
proves each change saved, and hands back a before/after table.

No skill can promise a video will "rank in the top". What this does is remove every packaging and
metadata reason it is not being found or clicked, then measure. Say that to the creator at the
start, once, in one sentence, and then do the work.

Needs: a signed-in Studio browser (creator signs in; never ask for a password), Python 3 for the
helper scripts (`py`/`python`), and `voice.md` filled in. Read `/yt-studio` before touching Studio.

## 0. Set up

1. Get the video ID. Open `https://studio.youtube.com/video/<ID>/edit`.
2. **Write the rollback record first**: current title, description, tags (with the `N/500`
   counter), monetization state and thumbnail, in the workspace. No record, no edits.
3. **Baseline**: from Studio analytics (Reach tab) note impressions, click-through rate, views and
   average view duration for the last 28 days, and the video's age. If it is new, say there is no
   baseline yet. These are the only numbers that decide whether the changes worked; do not invent
   any.
4. Decide the type: **new** (under about 48 hours, little data) or **underperforming** (older).
5. **Diagnose from the numbers before changing anything** with `/yt-diagnose` (Studio analytics,
   Reach tab, `/video/<ID>/analytics/tab-reach_viewers/period-default`), and for a video in a series
   run `/yt-series` to see whether its title and thumbnail are shared with every other episode.
   Fix the stage `diagnose.py` names first:
   - Many impressions but click-through under about 2%: the title or thumbnail is the problem.
   - Few impressions: discoverability is the problem (topic, title keywords, playlist/series
     placement).
   - Check **How viewers find this video**. If most views come from a playlist or channel page and
     almost none from search, the impressions are existing-audience impressions and search
     metadata will matter less than the title and thumbnail.
   Tested example: a series video had 47.2K impressions, 0.5% click-through, 347 views, 65%
   of views from the playlist and 4% from search. That is a packaging problem, not a keyword one.
6. **Check the Languages tab** (`/video/<ID>/translations`). If the video language is not English
   and an English title and description translation exists, English-language viewers may see the
   translated text rather than the one you edit. The translation row's menu only offers Delete;
   how to edit it is not yet verified, so report it to the creator instead of guessing.

## 1. Understand the video

Work out the one thing this video is about and the phrase a stranger would type to find it.

- Read the existing title, description and transcript if available (captions can be downloaded in
  Studio under Subtitles; not verified). If there is no transcript, read the video's own frames:
  `https://i.ytimg.com/vi/<ID>/hq1.jpg`, `hq2.jpg`, `hq3.jpg` are frames from 25%, 50% and 75% of
  the video and often show the problem or slide on screen.
- If the topic is still uncertain, ask the creator. **Never guess a problem name, a number or a
  claim.** A wrong title on a public video costs more than a plain one.
- Run `/yt-tags`'s `tags.py suggest` on the topic to see the real search phrases. The target query
  is the best-supported phrase that honestly describes the video.

## 2. Title (`/yt-package`)

Put the target query first, the series or channel name last, one clear promise, and keep it near 60
characters: `title.py` flags longer ones as cut off in desktop search, and a mobile feed shows less.
Lint with `title.py`. Do not use a claim the video does not
deliver, and do not retitle a video that is already performing well without the creator's say-so.

## 3. Description (`/yt-seo`)

- First two lines: what the viewer gets, in the words of the target query. They show before
  "...more" and are the search snippet.
- Then links, the previous and next video in the series, the playlist, chapters (step 5), then the
  longer description.
- **Keep what the creator already wrote that is theirs** (sponsor links, resources). Add around it,
  do not replace it.

## 4. Tags (`/yt-tags`)

Run `tags.py suggest` with `--existing` set to the current tags, plus `--avoid` and `--require`
when the seed is ambiguous. Audit existing tags first: tags copied from other videos are removed
(ask first). If nothing fits because the list is near 500 (tested: 482/500, nothing fit), swap:
drop the most redundant existing tags (for example several near-duplicates of one phrase), add the
better ones, and read the counter after each change, because removing a chip does not always
remove the one you meant. Match the video's spoken language (a Hindi video gained
`kruskal algorithm in hindi`). Never exceed the Studio counter: total = sum(len) + commas + 2 per tag with a space.
Type tags with real key presses, not by setting the field value.

## 5. Chapters and timeline (`/yt-chapters`)

YouTube only makes chapters if the list starts at `0:00`, has at least three entries, and each is
at least 10 seconds. Build them from a real transcript with `chapters.py`, or from timestamps the
creator gives. Never invent timestamps. Put them in the description and check Studio shows the
chapter markers on the timeline.

## 6. Monetization and mid-roll (`/yt-monetize`)

Run its audit on this video: ads on, mid-roll ticked, automatic slots on, any slot flagged as
unlikely to show ads. Tested example: a 14-minute video already had four automatic slots (about
1:37, 4:12, 6:42, 9:23) and none flagged, so nothing needed changing. Turn mid-roll on if the video
is eligible and it is off. Do not hand-place slots at guessed times. Report what YouTube chose.

## 7. Thumbnail

A thumbnail is the biggest click lever after the title, so treat it as a design job, not text.

**Assess the current thumbnail first.** View `https://i.ytimg.com/vi/<ID>/maxresdefault.jpg` at full
size and shrunk to about 170 px wide. Ask two questions: is it readable and clear, and **does it
say what THIS video is about?** Compare it with the neighbouring videos in the series. Tested
example: every video in a 100-video series shared one identical "DSA in 50 days" thumbnail. It was
clean and legible but carried no topic, so a viewer could not tell the videos apart, and a 14-minute
video sat at 0.5% click-through. Keep a thumbnail that is both clear and specific; replace one that
is clear but generic by keeping the brand (colours, the creator's own face art) and adding the
topic. Back up the original first (`.../maxresdefault.jpg` saved to the workspace).

Brief first (write it down before rendering):

- **One idea**, at most four big words. It adds to the title; it never repeats it.
- Readable at feed size: shrink the finished image to about 170 px wide and check it.
- High contrast, one focal point, one accent colour. Real face with a clear expression if the
  creator supplies a photo; do not generate people or fake screenshots.

Render with `thumbnail.template.html` in this folder: replace the `{{...}}` placeholders, open it
in a new browser page and save a PNG:

```
p = await page.context().newPage()
await p.setContent(html)
await p.screenshot({path: "<out>.png", fullPage: true, clip: {x:0, y:0, width:1280, height:720}})
```

Then **look at the image** before using it, including a zoom on any cropped edge: reusing the
creator's existing face art from the old thumbnail picked up fragments (a leftover subscribe-button
arc and part of a name banner) that had to be masked with `clip-path`. Show the creator the result
and let them choose. The file must be under 2 MB (a 1280x720 render was about 170 KB).

Upload, verified end to end on a real video: on `/video/<ID>/edit` open the thumbnail's
**Options** (three-dot) button, choose **Change**, and in the file chooser select the PNG
(Playwright: `waitForEvent('filechooser')`, then `setFiles(path)`). Studio previews it and enables
**Save**; save, reload and confirm the thumbnail changed. The same Options menu also offers
**Download**, **Select from video** and **A/B Testing**; for a video that is already doing well,
use A/B Testing instead of replacing the thumbnail outright.

## 8. What else moves a video up

These are the real ranking levers once the metadata is right. Do the ones Studio lets you do and
list the rest for the creator:

- **Playlist**: make sure the video is in the right series playlist, in order.
- **End screen and cards**: point to the next video in the series (set in Studio, Editor tab).
- **Pinned comment** with a question, and reply to early comments.
- **Share it** where the audience is (community post, other platforms). Early views matter most for
  a new video.
- **Fix the first 30 seconds** if retention shows people leave there. That is an editing change, not
  metadata; say so.

## 9. Verify and report

Use `/yt-studio`: save, reload the edit page, re-read every field. Then hand back one table: field,
before, after, verified yes/no. Set a re-check date 14 days out and say which three numbers to
compare (impressions, click-through rate, average view duration). If click-through did not rise,
the title or thumbnail is the next thing to change; if impressions rose but views did not, the
thumbnail; if people leave early, the video itself.

## The gate

Nothing here publishes a new video. Show the full plan for this one video, get one yes, apply it,
verify it. The last line of every run is the question: **ship it, or change it?**
