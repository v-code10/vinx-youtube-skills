---
name: yt-diagnose
description: >-
  Find the one thing holding a video back from its Studio numbers: not shown, not clicked, or not
  watched. Use for "why isn't this video growing", "what should I fix first", or before touching a
  video's title, thumbnail or tags.
---

# yt-diagnose

A video is limited by three stages in order: it has to be **shown** (impressions), then **clicked**
(click-through rate), then **watched** (average view duration). Fixing a later stage before an
earlier one wastes the work, so find the first broken one.

## Steps

1. In Studio open the video's Analytics, Reach tab. Record impressions, click-through rate, views,
   the share of views from search and from playlists, and (Engagement tab) average view duration and
   video length. Write down only what you read.
2. Run:

   ```
   python3 diagnose.py --impressions 47200 --ctr 0.5 --views 347 --length 14:00 \
       --search-share 4 --playlist-share 65 --avd 3:10 --channel-ctr 3
   ```

   `--channel-ctr` is the channel's usual click-through; without it a generic 4% is used.
3. Read the first line it prints and fix only that stage. Hand the result to `/yt-boost`.

## Tested example

A 14-minute series video: 47.2K impressions, 0.5% click-through, 347 views, 65% of views from the
playlist, 4% from search. The tool reports "not clicked" first and notes the audience is mostly the
existing playlist audience, so the title and a topic-specific thumbnail are the lever, not tags.

## Limits

The thresholds are rules of thumb, not YouTube's. Click-through naturally runs lower on videos
shown mostly inside a playlist or to subscribers, so compare with the channel's own median.
