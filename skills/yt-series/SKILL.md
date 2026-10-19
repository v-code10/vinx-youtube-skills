---
name: yt-series
description: >-
  Audit a whole playlist or numbered series: titles with no topic, duplicate or missing episode
  numbers, one thumbnail reused across every episode, empty descriptions. Use for "audit my
  playlist", "why do my series videos all look the same", or before running /yt-boost across many
  videos.
---

# yt-series

Series fail in a pattern the single-video skills cannot see: every episode gets the same thumbnail
and a title that is only the series name plus a number, so nothing tells a viewer one episode from
the next. This finds that, with no model involved.

## Run it

```
python3 series.py --playlist <PLAYLIST_ID> --thumbs
python3 series.py --file videos.tsv --thumbs        # video_id<TAB>title[<TAB>description]
```

`--playlist` reads the public playlist page (first 100 videos). For a longer playlist or to include
descriptions, export `id<TAB>title<TAB>description` lines and use `--file`. Add
`--series-words "mychannel,mycourse"` for words that belong to the series, not the topic.

## What it reports

- titles with no topic, so you know which videos need a topic-first title
- duplicate and missing episode numbers
- how many distinct thumbnails the series uses, and how many episodes share the most-used one
- empty descriptions and descriptions without the playlist link (file mode)

## Then

Fix the worst class first. Topic-less titles go to `/yt-boost` one video at a time, starting with
the weakest performers. If one thumbnail covers the whole series, plan topic-specific thumbnails
with the same brand (colours and face) and test them with Studio's A/B Testing, not all at once.
Never invent a topic for a title: ask the creator for it or read it from the video.
