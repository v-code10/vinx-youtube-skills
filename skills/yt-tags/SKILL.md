---
name: yt-tags
description: >-
  Find tags people actually search for on a specific video and add them without ever going over
  Studio's 500-character limit. Use for "tags", "better tags", "viral tags", "update the tags on
  this video", or when a save fails with "Cannot save until errors are resolved".
---

# yt-tags

Two jobs: pick tags from real search demand, and make sure what you hand over saves.

## The counter (verified, do not guess it)

Studio's tag counter is not a character count:

    total = sum(len(tag)) + (tags - 1) commas + 2 for every tag containing a space

Checked against Studio's own numbers: 27 tags showed 442/500 and 29 tags showed 500/500, and the
formula reproduces both exactly. Over 500 and the video will not save. `tags.py count` and
`tags.py fit` apply this rule, so use them instead of eyeballing.

## Steps

1. Read the video's title, description and, if you have it, the transcript. Pick 2-4 seed phrases:
   the topic as a person would type it ("number of islands leetcode python"), not the channel's
   own vocabulary.
2. Read the video's **existing tags** from Studio (Details > Show more). Never start from an empty
   list: existing tags are the creator's, and the new list must keep them. **Audit them first**:
   on a real channel, a video's tags were copied from other videos (a "subarray sum" tag on a
   "max consecutive ones" video) and the list was already at 500/500, which is why adding tags
   failed. List any tag that belongs to a different topic and ask before removing it.
3. Run:

   ```
   python3 tags.py suggest --seed "seed one,seed two" --existing "<existing tags, comma separated>" --max-new 8
   ```

   It asks YouTube's search autocomplete what people type after each seed, ranks by how often and
   how high each phrase appears, drops what is already there, and adds only what fits.
   Add `--avoid "java,c++"` to drop other languages, and `--require "leetcode,python,dsa"` when a
   seed is ambiguous: "sliding window" on its own suggests house windows.
4. If nothing fits, say so and propose which weakest existing tags to drop. Do not remove tags
   without the creator agreeing.
5. Hand over the final list and the `Studio will show N/500` line. Apply it with `/yt-studio`.

## What "viral tags" can and cannot mean

Autocomplete tells you what people search. It does not predict views, and YouTube has said tags are
a weak signal. Spend the tags on spellings, tool names and the phrases people really type. Do not
add unrelated trending words: that is against YouTube's spam policy and it will not help.

## The gate

Nothing here publishes. Every output ends in the exact tag line to paste, and the last line of
every run is the question: **ship it, or change it?**
