---
name: chickener-image
description: Generate images (up to 4K, 3840x2160) through the chickener.top API with gpt-image-2 or gpt-image-2.5. Use when the user asks to draw, generate, create or render an image, picture, poster, wallpaper, illustration or photo, or mentions 生图 / 画图 / 出图 / 4K 图片.
---

# chickener-image

Generate images through chickener.top. Everything runs through one script:
`scripts/gen_image.py` (Python 3.8+, standard library only). It lives in this
skill's own folder; resolve the path relative to this SKILL.md.

On Windows try `python`, then `py -3`; on macOS/Linux use `python3`. If none
prints `Python 3.x`, or Windows opens the Microsoft Store / says "Python was
not found", Python is missing: walk the user through section 0 of this skill's
`README.md`, step by step. Remind them to tick "Add python.exe to PATH" on
Windows and to restart the terminal and the agent after installing.

## Step 1 — make sure the API key works (do this first, every new session)

```bash
python scripts/gen_image.py --check
```

- `OK: ready` → go to step 2.
- `API key is not configured` → walk the user through **Configure the API key**
  in this skill's `README.md` (section 2). Short version:
  1. Log in to https://chickener.top/keys (sidebar: **API 密钥**) → **创建 API 密钥**.
  2. Set **分组** to **【GPT】生图分组**. Other groups cannot draw images.
  3. Click **复制密钥** (the key starts with `sk-`) and paste it to you.
  4. Save it with `python scripts/gen_image.py --set-key <key>`, then run `--check` again.
- Any other `ERROR` / `HINT` line → explain it to the user in plain words and
  follow the hint.

Key rules:
- The key is stored in `~/.chickener/config.json`. Never print the key, never
  write it anywhere else (no project files, no notes, no git).
- If the user pastes the key in chat, save it with `--set-key` and tell them
  once: the key is now in this chat history; they can regenerate it on the
  token page if that worries them.

## Step 2 — generate

```bash
python scripts/gen_image.py --prompt "<prompt>" --size <size> [--model gpt-image-2.5] [--out <folder or file.png>]
```

Size: pick from what the user asked for.

| User asks for | `--size` |
| --- | --- |
| 4K, landscape / 16:9 / wallpaper (default for "4K") | `4k` (3840x2160) |
| 4K portrait / phone wallpaper / 9:16 | `4k-portrait` (2160x3840) |
| 2K | `2k` (2560x1440) or `2k-portrait` |
| nothing specific | `1024x1024` (default) |
| a specific ratio | `WIDTHxHEIGHT`, longest side ≤ 3840, both sides multiples of 16 |

Other options:
- `--model`: `gpt-image-2` (default) or `gpt-image-2.5`. Use the one the user names.
- `--quality`: `high` (default). Leave it unless the user asks otherwise.
- `--n`: 1-4 images (default 1).
- `--out`: default is `./chickener-images/` in the current folder.

A 4K image takes about 20-60 seconds. Tell the user it is working, and give
the command a timeout of at least 10 minutes. Do not retry while it is running.

When it finishes, the script prints `SAVED: <path> (actual size WxH, ...)`.
Tell the user the file path and the actual size. If the actual size differs
from what was requested, say so plainly instead of claiming success.

## Prompt tips

Write the prompt in the user's language or English, describing subject,
style, composition and lighting. For text inside the image, quote the exact
words. Do not add extra content the user did not ask for.
