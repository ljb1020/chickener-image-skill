#!/usr/bin/env python3
"""Generate images with chickener.top (gpt-image-2 / gpt-image-2.5, up to 4K).

Standard library only. Messages are plain English on purpose: the calling
agent reads them and explains to the user in their own language.

Usage:
  python gen_image.py --check
  python gen_image.py --set-key sk-xxxx
  python gen_image.py --prompt "a cat" --size 4k
"""

import argparse
import base64
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.request

VERSION = "1.0.0"
DEFAULT_BASE_URL = "https://chickener.top"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".chickener", "config.json")
MODELS = ("gpt-image-2", "gpt-image-2.5")
SIZE_ALIASES = {
    "4k": "3840x2160",
    "4k-landscape": "3840x2160",
    "4k-portrait": "2160x3840",
    "2k": "2560x1440",
    "2k-portrait": "1440x2560",
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
}
# Cloudflare in front of the site rejects the default Python-urllib agent (error 1010).
USER_AGENT = "chickener-image-skill/" + VERSION
GENERATE_TIMEOUT_SECONDS = 600
# The exact Chinese group name is in README.md section 2; keep script output ASCII.
TOKEN_GROUP = "the [GPT] image-generation group named in README.md section 2"


def fail(message, hint=None, code=1):
    print("ERROR: " + message)
    if hint:
        print("HINT: " + hint)
    sys.exit(code)


def mask(key):
    return key[:5] + "..." if len(key) > 5 else "***"


def load_config():
    if not os.path.isfile(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        fail("config file is not valid JSON: %s (%s)" % (CONFIG_PATH, e),
             'The file must look exactly like: {"api_key": "sk-..."}  '
             "Re-run with --set-key to rewrite it.")
    return data if isinstance(data, dict) else {}


def resolve_key():
    env_key = os.environ.get("CHICKENER_API_KEY", "").strip()
    if env_key:
        return env_key, "environment variable CHICKENER_API_KEY"
    key = str(load_config().get("api_key", "")).strip()
    if key and not key.startswith("sk-xxxx"):
        return key, CONFIG_PATH
    fail("API key is not configured.",
         "Create a token on https://chickener.top (token group: %s), then run:\n"
         "      python gen_image.py --set-key sk-YOUR-KEY\n"
         "  or write {\"api_key\": \"sk-YOUR-KEY\"} into %s" % (TOKEN_GROUP, CONFIG_PATH))


def resolve_base_url():
    base = os.environ.get("CHICKENER_BASE_URL", "").strip() or str(load_config().get("base_url", "")).strip()
    return (base or DEFAULT_BASE_URL).rstrip("/")


def set_key(key):
    key = key.strip().strip('"').strip("'")
    if not key.startswith("sk-") or len(key) < 20 or re.search(r"\s", key):
        fail("this does not look like a chickener API key (expected sk-..., no spaces).",
             "Copy the whole key from the token page again.")
    config = load_config()
    config["api_key"] = key
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    if os.name != "nt":
        os.chmod(CONFIG_PATH, 0o600)
    print("OK: key %s saved to %s" % (mask(key), CONFIG_PATH))
    print("NEXT: run --check to verify it.")


def request(method, url, key, body=None, timeout=60):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        fail("cannot reach %s (%s)" % (url, e.reason), "Check the network connection, then retry.")
    except TimeoutError:
        fail("request timed out after %d seconds." % timeout,
             "4K images usually take 20-60 seconds; retry once. If it keeps timing out, try a smaller size.")


def error_message(text):
    try:
        err = json.loads(text).get("error")
    except (ValueError, AttributeError):
        return text.strip()[:300]
    if isinstance(err, dict):
        return str(err.get("message") or err.get("code") or err)[:300]
    return str(err or text)[:300]


def explain_http_error(status, text):
    message = error_message(text)
    lowered = message.lower()
    if status == 401:
        fail("the API key was rejected (HTTP 401): " + message,
             "The key is wrong, deleted or disabled. Copy it again from the token page and run --set-key.")
    if status == 403 and "1010" in message:
        fail("blocked by the site firewall (HTTP 403, Cloudflare 1010).",
             "Update this skill to the latest version; it must send its own User-Agent.")
    if "model_not_found" in lowered or "no available channel" in lowered or "无可用渠道" in message:
        fail("the token cannot use this model (HTTP %d): %s" % (status, message),
             "Set the token's group to %s on the token page." % TOKEN_GROUP)
    if "quota" in lowered or "额度" in message or "余额" in message:
        fail("not enough balance or token quota (HTTP %d): %s" % (status, message),
             "Top up the account or raise the token's quota on chickener.top.")
    if status == 429:
        fail("rate limited (HTTP 429): " + message, "Wait a minute and retry.")
    fail("request failed (HTTP %d): %s" % (status, message))


def check():
    key, source = resolve_key()
    base = resolve_base_url()
    print("key: %s (from %s)" % (mask(key), source))
    print("site: " + base)
    status, text = request("GET", base + "/v1/models", key)
    if status != 200:
        explain_http_error(status, text)
    try:
        models = sorted(m.get("id", "") for m in json.loads(text).get("data", []))
    except (ValueError, AttributeError):
        fail("unexpected response from /v1/models: " + text[:200])
    usable = [m for m in MODELS if m in models]
    print("models visible to this token: " + (", ".join(models) or "(none)"))
    if not usable:
        fail("this token cannot see any image model.",
             "Set the token's group to %s on the token page, then run --check again." % TOKEN_GROUP)
    print("OK: ready. Image models: " + ", ".join(usable))


def normalize_size(size):
    size = size.strip().lower().replace("×", "x").replace("*", "x")
    size = SIZE_ALIASES.get(size, size)
    match = re.fullmatch(r"(\d+)x(\d+)", size)
    if not match:
        fail("invalid --size %r." % size,
             "Use WIDTHxHEIGHT such as 3840x2160, or one of: " + ", ".join(SIZE_ALIASES))
    width, height = int(match.group(1)), int(match.group(2))
    if max(width, height) > 3840:
        fail("size %s is larger than 4K; the longest side must be <= 3840." % size,
             "Use 3840x2160 (landscape) or 2160x3840 (portrait).")
    return size


def png_size(raw):
    if raw[:8] == b"\x89PNG\r\n\x1a\n" and len(raw) >= 24:
        return "%dx%d" % struct.unpack(">II", raw[16:24])
    return "unknown"


def output_path(out, index, count):
    if out and out.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        if count == 1:
            return out
        stem, ext = os.path.splitext(out)
        return "%s_%d%s" % (stem, index + 1, ext)
    folder = out or os.path.join(os.getcwd(), "chickener-images")
    suffix = "" if count == 1 else "_%d" % (index + 1)
    return os.path.join(folder, "image_%s%s.png" % (time.strftime("%Y%m%d_%H%M%S"), suffix))


def generate(args):
    if not args.prompt or not args.prompt.strip():
        fail("--prompt is required.")
    if args.n < 1 or args.n > 4:
        fail("--n must be between 1 and 4.")
    size = normalize_size(args.size)
    key, _ = resolve_key()
    base = resolve_base_url()
    body = {"model": args.model, "prompt": args.prompt, "size": size, "quality": args.quality, "n": args.n}
    print("generating: model=%s size=%s quality=%s n=%d (4K usually takes 20-60s, please wait)"
          % (args.model, size, args.quality, args.n))
    sys.stdout.flush()
    started = time.time()
    status, text = request("POST", base + "/v1/images/generations", key, body, GENERATE_TIMEOUT_SECONDS)
    if status != 200:
        explain_http_error(status, text)
    try:
        items = json.loads(text).get("data") or []
    except (ValueError, AttributeError):
        fail("unexpected response: " + text.strip()[:300])
    if not items:
        fail("the response contained no image: " + text.strip()[:300])
    for index, item in enumerate(items):
        if item.get("b64_json"):
            raw = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            img_req = urllib.request.Request(item["url"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(img_req, timeout=120) as resp:
                raw = resp.read()
        else:
            fail("image %d has neither b64_json nor url." % (index + 1))
        path = os.path.abspath(output_path(args.out, index, len(items)))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(raw)
        print("SAVED: %s (actual size %s, %d KB)" % (path, png_size(raw), len(raw) // 1024))
    print("done in %.0fs" % (time.time() - started))


def main():
    # Paths (e.g. a Chinese Windows user name) and server messages may be non-ASCII.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Generate images with chickener.top (up to 4K).")
    parser.add_argument("--check", action="store_true", help="verify the API key and token group")
    parser.add_argument("--set-key", metavar="KEY", help="save the API key to " + CONFIG_PATH)
    parser.add_argument("--prompt", help="what to draw")
    parser.add_argument("--size", default="1024x1024",
                        help="WIDTHxHEIGHT or alias: " + ", ".join(SIZE_ALIASES) + " (default 1024x1024)")
    parser.add_argument("--model", default="gpt-image-2", choices=MODELS)
    parser.add_argument("--quality", default="high", choices=("low", "medium", "high", "auto"))
    parser.add_argument("--n", type=int, default=1, help="number of images, 1-4 (default 1)")
    parser.add_argument("--out", help="output folder, or a file path ending in .png")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args()

    if args.set_key:
        set_key(args.set_key)
    elif args.check:
        check()
    else:
        generate(args)


if __name__ == "__main__":
    main()
