---
name: yt-studio
description: >-
  Edit a video's title, description, tags or settings in YouTube Studio through a signed-in browser
  and prove the change saved. Use whenever another skill hands over text to apply, or for "update
  the video", "change the title", "apply these tags".
---

# yt-studio

Written after a bulk run reported videos as saved when Studio had silently refused them. The rule:
**a save is only real once you have reloaded the page and read the value back.**

## Before touching anything

1. The creator signs in themselves in the browser you control. Never type or ask for a password.
2. Record the original title, description and tags (a rollback file in the workspace) **before**
   editing. Without that there is no undo.
3. Work on one video, show the creator the result, then batch. Never start with a bulk run.

## Editing one video

Verified selectors on `https://studio.youtube.com/video/<ID>/edit`:

- Title: `#title-textarea #textbox`; description: `#description-textarea #textbox`. Click, select
  all, type. Do not append, or you duplicate.
- Tags are under **Show more** (`ytcp-button#toggle-button`). Add a tag by **typing** it followed by
  a comma with real key presses (`page.keyboard.type("tag,")`). Setting the field's value (`fill`)
  leaves the text sitting uncommitted in the box, the counter does not move and nothing is saved.
  Remove a tag with the Remove button inside its chip. The counter reads like `442/500`.
- Save button: role `button`, name `Save`.

## Tags: never exceed the counter

Run `yt-tags` first. Add tags one at a time and read the `N/500` counter after each; if it goes over,
remove that last tag. Over 500 puts "Cannot save until errors are resolved" on the page and the
Save button stays disabled, which looks the same as "already saved". That ambiguity caused false
"done" reports, so never infer success from the button being disabled.

## Prove it saved

After Save:

1. Wait for the "Changes saved" toast.
2. Navigate away (accept the "unsaved changes" prompt only now) and **reload the edit page**.
3. Read title, description and the tag counter again and compare with what you intended. Only then
   report "done". If they differ, report the video as failed with what you saw.

## Pitfalls seen in practice

- Navigating from a page with unsaved edits raises a `beforeunload` dialog and can leave the next
  navigation hanging. Retry the navigation up to three times after the first failure.
- Playlist and channel pages can show a stale title for a while. Verify in Studio's own edit page,
  not on a public page.
- Do not change a video that is already doing well without the creator's say-so.

## The gate

Nothing here publishes a new video. Every batch ends with a table of video, old value, new value,
verified yes/no, and the question: **ship it, or change it?**
