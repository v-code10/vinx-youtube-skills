---
name: yt-monetize
description: >-
  Earn more from mid-roll ads without fighting YouTube: audit which videos have ads on, turn on
  YouTube's automatic placement, and shape new videos so it finds more natural breakpoints. Use for
  "add mid-roll ads", "ad breaks", "monetize this video", "earn more", "where should ads go".
---

# yt-monetize

YouTube decides where mid-roll ads can actually run. Tested on a real channel: every manual slot
placed at an evenly spaced time was marked "unlikely to show ads" by Studio, while YouTube's own
automatic slots were not. So this skill follows YouTube's placement and earns more by **covering
every eligible video** and **giving YouTube more natural breakpoints to choose from**.

YouTube's Data API cannot change ad settings, so this drives Studio in a browser the creator is
already signed in to (use `/yt-studio` for the save-and-verify procedure).

## What actually raises earnings here

1. **Mid-roll is on for every eligible video.** Eligibility is normally 8+ minutes and a channel in
   the YouTube Partner Programme. A video with it off earns nothing from breaks.
2. **Automatic ad slots stay on.** They are the slots YouTube knows will show ads.
3. **Videos have clear natural breakpoints.** YouTube places ads at pauses and topic changes. A
   video that runs as one unbroken talk gives it little to pick; a video with a clean break every
   few minutes gives it more. This is the lever you control when you record and edit.
4. **Length.** More minutes past 8 means more breakpoints. Do not pad: it costs retention, and
   retention drives the next video's views.

## Audit (do this first)

For each video, open `https://studio.youtube.com/video/<VIDEO_ID>/monetization/ads` and record:

- is the checkbox **Show mid-roll ads during my video** ticked,
- the slots listed under **Review mid-roll placement** (`Ad slot (Automatic)` or `(Manual)`, time
  in `MM:SS:FF`) and whether any shows the warning "Places like natural breakpoints ... unlikely to
  show ads".

Report a table: video, length, mid-roll on/off, number of slots, flagged slots. Videos under about
8 minutes may not offer the setting; say so rather than treating it as a failure.

## Turn it on

If mid-roll is off on an eligible video, show the list and get the creator's yes once, then tick
the checkbox and save with `/yt-studio`. Re-open the page afterwards and confirm it stayed on.

## Do not hand-place slots blindly

- Never edit or delete an `Automatic` slot: Studio asks "Turn off automatic ad slots?" and turns
  every automatic slot into a manual one. Press Cancel.
- Manual slots are only worth adding at a real pause. After saving, reopen the dialog; if the slot
  shows the warning, remove it. Rows re-sort by time, so find a row by its `Manual`/`Automatic`
  label, never by position. Allow several seconds after a reload for the review to appear.
- The dialog: **Insert ad slot** adds a Manual slot at `00:00:00`; type the time in `MM:SS:FF`;
  **Continue** applies it; **Discard changes** drops it. Videos over an hour: time format not
  checked.

## Shape new videos for more breakpoints

`midroll.py` turns a length into a target density, one formula for any video:

    ads = floor((duration - 60s tail - first) / gap) + 1

```
python3 midroll.py --duration 20:00                       # earn: 5 breaks, every 4:00 from 1:30
python3 midroll.py --duration 20:00 --mode balanced       # 4 breaks
python3 midroll.py --duration 58:03 --srt transcript.srt  # moves each to the nearest real pause
```

| mode | first | gap | breaks in 20 min |
|---|---|---|---|
| `earn` (default) | 1:30 | 4:00 | 5 |
| `balanced` | 2:00 | 5:00 | 4 |
| `viewer` | 3:00 | 8:00 | 2 |

Use the output as **editing marks, not ad times**: at each timestamp, end a section with a clear
beat, a one-second pause and a topic change ("that's the brute force; now the optimised one").
Those are the moments YouTube's automatic placement can use. Then check the video's slots after
publish. Do not claim a number of ads will run; YouTube decides, and the audit shows what it chose.

More breaks earn more per view and usually cost watch time. After a week compare average view
duration with the creator's usual, and drop to `balanced` if it fell noticeably.

## The gate

Ads change what viewers see and what the channel earns. Show the audit and the plan, get a yes,
then apply. The last line of every run is the question: **ship it, or change it?**
