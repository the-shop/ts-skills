#!/usr/bin/env python3
"""Deterministic keyed-facts merge for handoff briefs.

A later write to a key retires the older line, so a successor never sees an old rule next to its
replacement. Usage:

    merge_facts.py NEW_DRAFT [--prev RECEIVED_BRIEF] [--as-of STAMP]

The draft carries its facts between the exact lines <<<FACTS v1>>> and <<<END FACTS>>>. Prints the
final brief: the verbatim request block (carried from --prev when given, else from the draft), the
draft body, then the merged FACTS, SUPERSEDED and EVICTED blocks. Warnings go to stderr.
"""
import argparse
import datetime
import re
import sys

# Machine delimiters: only text between them is parsed; headings anywhere else are plain body text.
FACTS_BEGIN = "<<<FACTS v1>>>"
FACTS_END = "<<<END FACTS>>>"
SUPERSEDED_BEGIN = "<<<SUPERSEDED>>>"
SUPERSEDED_END = "<<<END SUPERSEDED>>>"
EVICTED_BEGIN = "<<<EVICTED>>>"
EVICTED_END = "<<<END EVICTED>>>"
REQUEST_END = "<<<END REQUEST>>>"
SUPERSEDED_LABEL = "(audit only, NOT current)"
EVICTED_LABEL = "(dropped over the fact cap, newest first)"
MAX_SUPERSEDED = 12
MAX_EVICTED = 12
MAX_ACTIVE = 60

BULLET_RE = re.compile(r"^\s*[-*•]\s+([^:\n]{1,80}?)\s*:\s+(.+?)\s*$")
AS_OF_RE = re.compile(r"\s*\(as-of:\s*([^)]*)\)\s*$")
REQUEST_RE = re.compile(r"^[ \t]*<<<REQUEST n_lines=(\d+)>>>[ \t]*$", re.M)


def norm_key(k):
    """Only case, surrounding whitespace and runs of space/_/- are normalised (c++ vs c stay apart)."""
    return re.sub(r"[\s_-]+", "-", k.strip().lower()).strip("-")


def is_retired(v):
    return bool(re.match(r"^RETIRED\.?$", re.sub(r"^[`*\"']+|[`*\"']+$", "", v.strip()).strip()))


def _fact(key, raw, as_of):
    stamp = AS_OF_RE.search(raw)
    return {"key": key.strip(), "value": AS_OF_RE.sub("", raw).strip(),
            "as_of": (stamp.group(1).strip() if stamp else "") or as_of}


BODY_NOTE = f'NOTE: "key: value" lines in the body below may be stale; the {FACTS_BEGIN} block is authoritative.'


PLACEHOLDERS = {"<key>", "<another-key>", "<value>"}


def _is_placeholder(k, v):
    """The documented example strings; a copy of them is never a fact (<redacted> etc. are real values)."""
    return k.strip() in PLACEHOLDERS or AS_OF_RE.sub("", v).strip() in PLACEHOLDERS


def body_conflicts(body, active):
    """Fact-like body bullets outside the block: keys repeating an active fact, plus anything under a legacy
    'FACTS:' heading. Each is a second, possibly stale copy."""
    keys = {norm_key(a["key"]) for a in active}
    found = []
    for line in body.split("\n"):
        hit = BULLET_RE.match(line)
        if hit and norm_key(hit.group(1)) in keys:
            found.append(hit.group(1))
    found += [f["key"] for f in _legacy_parse(body, "?")["active"]]
    out = []
    for k in found:
        if k.strip() not in out:
            out.append(k.strip())
    return out


def _last_per_key(facts):
    """Later lines win per key (first position kept), so several blocks behave like one rewritten list."""
    out = []
    for f in facts:
        i = next((n for n, o in enumerate(out) if norm_key(o["key"]) == norm_key(f["key"])), -1)
        if i >= 0:
            out[i] = f
        else:
            out.append(f)
    return out


def parse_fact_lines(lines, as_of, dropped=None):
    """'- key: value' bullets; an indented line continues the previous value; anything else is reported."""
    dropped = [] if dropped is None else dropped
    out = []
    for line in lines:
        t = line.strip()
        hit = BULLET_RE.match(line)
        if hit and norm_key(hit.group(1)) != "" and not _is_placeholder(hit.group(1), hit.group(2)):
            out.append([hit.group(1), hit.group(2)])
        elif t == "" or re.match(r"^`{3,}\w*$", t):
            continue
        elif not hit and re.match(r"^\s", line) and out:
            stamp = AS_OF_RE.search(out[-1][1])
            out[-1][1] = f"{AS_OF_RE.sub('', out[-1][1])} {t}{stamp.group(0) if stamp else ''}"
        else:
            dropped.append(t)
    return [_fact(k, r, as_of) for k, r in out]


def parse_facts(lines, as_of):
    return parse_fact_lines(list(lines), as_of)


def _is_delim(line, d):
    return re.sub(r"^[`*]+|[`*]+$", "", line.strip()) == d


def take_blocks(text, begin, end):
    """Every begin..end block in order -> (blocks, rest, is_unterminated); an unterminated block runs to the end."""
    blocks, rest, cur = [], [], None
    for line in text.split("\n"):
        if cur is None and _is_delim(line, begin):
            cur = []
            blocks.append(cur)
        elif cur is not None and _is_delim(line, end):
            cur = None
        else:
            (rest if cur is None else cur).append(line)
    return blocks, "\n".join(rest), cur is not None


def merge(prev_active, prev_superseded, new, max_superseded=MAX_SUPERSEDED, max_active=MAX_ACTIVE, evicted=None):
    """-> (active, superseded); facts dropped over the active cap are appended to `evicted`."""
    active, superseded, touched = list(prev_active), list(prev_superseded), set()
    for f in new:
        k = norm_key(f["key"])
        i = next((n for n, a in enumerate(active) if norm_key(a["key"]) == k), -1)
        old = active[i] if i >= 0 else None
        touched.add(k)
        if is_retired(f["value"]):
            if old:
                superseded.append(old)
                del active[i]
        elif old is None:
            active.append(f)
        elif old["value"] != f["value"]:
            superseded.append(old)
            active[i] = f
    # Over the cap, facts this merge did not touch leave first (oldest position first), then the oldest of the rest.
    evicted = [] if evicted is None else evicted
    i = 0
    while len(active) > max_active and i < len(active):
        if norm_key(active[i]["key"]) not in touched:
            evicted.append(active.pop(i))
        else:
            i += 1
    if len(active) > max_active:
        evicted += active[:len(active) - max_active]
        active = active[len(active) - max_active:]
    return active, superseded[-max_superseded:]


def trace_evictions(newly, prev_traces, as_of, max_active=MAX_ACTIVE):
    """Eviction traces live in their own list (newest first) so they never push real supersedes out."""
    trace = [dict(e, as_of=f"evicted {as_of}, cap {max_active}; set {e['as_of']}") for e in newly]
    return (trace + list(prev_traces))[:MAX_EVICTED]


def render(active, superseded, evicted=()):
    line = lambda f: f"- {f['key']}: {f['value']} (as-of: {f['as_of']})"
    out = [FACTS_BEGIN] + [line(f) for f in active] + [FACTS_END]
    if superseded:
        out += ["", SUPERSEDED_LABEL, SUPERSEDED_BEGIN] + [line(f) for f in superseded] + [SUPERSEDED_END]
    if evicted:
        out += ["", EVICTED_LABEL, EVICTED_BEGIN] + [line(f) for f in evicted] + [EVICTED_END]
    return "\n".join(out)


def render_request(request):
    if not request or not request.strip():
        return []
    return [f"<<<REQUEST n_lines={len(request.split(chr(10)))}>>>", request, REQUEST_END, ""]


def parse_request(text):
    """-> (request or None, rest). Line-counted; a wrong count falls back to the last END line."""
    hit = REQUEST_RE.search(text)
    if not hit:
        return None, text
    n = int(hit.group(1))
    lines = text[hit.end() + 1:].split("\n")
    end = n if n < len(lines) and lines[n].strip() == REQUEST_END else -1
    if end < 0:
        end = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].strip() == REQUEST_END), -1)
    if end < 0:
        return "\n".join(lines), text[:hit.start()]
    return "\n".join(lines[:end]), text[:hit.start()] + "\n".join(lines[end + 1:])


def parse_brief(text, as_of, allow_legacy=False):
    """-> dict(request, body, active, superseded, evicted, warnings, has_facts)."""
    warnings, dropped = [], []
    request, rest = parse_request(text)
    f_blocks, rest, unterminated = take_blocks(rest, FACTS_BEGIN, FACTS_END)
    if not f_blocks and allow_legacy:
        legacy = _legacy_parse(text, as_of)
        if legacy["request"] is not None or legacy["active"] or legacy["superseded"]:
            warnings.append(f"no {FACTS_BEGIN} block; read with the legacy heading parser")
            return dict(legacy, warnings=warnings, has_facts=bool(legacy["active"]))
    if unterminated:
        warnings.append(f"{FACTS_BEGIN} has no {FACTS_END}; read to the end of the text")
    if len(f_blocks) > 1:
        warnings.append(f"found {len(f_blocks)} {FACTS_BEGIN} blocks; merged in order, last wins per key")
    s_blocks, rest, _ = take_blocks(rest, SUPERSEDED_BEGIN, SUPERSEDED_END)
    e_blocks, rest, _ = take_blocks(rest, EVICTED_BEGIN, EVICTED_END)
    flat = lambda bs: [l for b in bs for l in b]
    active = _last_per_key(parse_fact_lines(flat(f_blocks), as_of, dropped))
    warnings += [f'dropped non "key: value" fact line: {d}' for d in dropped]
    labels = r'^(?:\((?:audit only, NOT current|dropped over the fact cap, newest first)\)|NOTE: "key: value" lines in the body below may be stale;.*)$'
    body = re.sub(labels, "", rest, flags=re.M).strip()
    conflicts = body_conflicts(body, active)
    if allow_legacy and conflicts:
        warnings.append(f"body has fact-like lines outside the block ({', '.join(conflicts)}); the {FACTS_BEGIN} block is authoritative")
    return {"request": request, "body": body, "active": active, "superseded": parse_fact_lines(flat(s_blocks), as_of),
            "evicted": parse_fact_lines(flat(e_blocks), as_of), "warnings": warnings, "has_facts": bool(f_blocks)}


def split(text, as_of):
    """-> (request or None, body, facts, superseded)."""
    p = parse_brief(text, as_of, allow_legacy=True)
    return p["request"], p["body"], p["active"], p["superseded"]


def compose(new_text, prev_text, as_of, warnings=None):
    """-> brief; warnings (dropped lines, missing FACTS block, cap evictions) are appended to `warnings`."""
    warnings = [] if warnings is None else warnings
    prev = parse_brief(prev_text, "?", allow_legacy=True) if prev_text else None
    if prev:
        warnings += [f"received brief: {w}" for w in prev["warnings"]]
    new = parse_brief(new_text, as_of)
    warnings += new["warnings"]
    if not new["has_facts"] and any(BULLET_RE.match(l) for l in new["body"].split("\n")):
        warnings.append(f'WARNING: no {FACTS_BEGIN} block in the new brief; its "key: value" bullets were NOT adopted, predecessor facts kept unchanged')
    newly = []
    active, superseded = merge(prev["active"] if prev else [], prev["superseded"] if prev else [],
                               new["active"] if new["has_facts"] else [], evicted=newly)
    evicted = trace_evictions(newly, prev["evicted"] if prev else [], as_of)
    warnings += [f"evicted over {MAX_ACTIVE}-fact cap: {f['key']}" for f in newly]
    request = prev["request"] if prev and prev["request"] is not None else new["request"]
    conflicts = body_conflicts(new["body"], active)
    if conflicts:
        warnings.append(f"body has fact-like lines outside the block ({', '.join(conflicts)}); noted in the brief that the FACTS block is authoritative")
    body = f"{BODY_NOTE}\n{new['body']}" if conflicts else new["body"]
    out = render_request(request) + ([body, ""] if body else []) + [render(active, superseded, evicted)]
    return "\n".join(out) + "\n"


# Pre-delimiter format (heading "FACTS:", "SUPERSEDED (...):", "ORIGINAL USER REQUEST (verbatim[, N lines]):"). Read only.
LEGACY_REQUEST_RE = re.compile(r"^ORIGINAL USER REQUEST \(verbatim(?:, (\d+) lines?)?\):$", re.M)
LEGACY_REQUEST_END = "END ORIGINAL USER REQUEST"
LEGACY_FACTS_RE = re.compile(r"^[#*\s]*(?:\d+[.)]\s*)?(?:key\s+)?facts\s*:?\s*\**\s*$", re.I)
LEGACY_SUPERSEDED_RE = re.compile(r"^[#*\s]*(?:\d+[.)]\s*)?superseded(?:\s+facts)?\s*(?:\([^)]*\))?\s*:?\s*\**\s*$", re.I)


def _legacy_parse(text, as_of):
    request, rest = None, text
    hit = LEGACY_REQUEST_RE.search(text)
    if hit:
        lines = text[hit.end() + 1:].split("\n")
        n = int(hit.group(1)) if hit.group(1) is not None else -1
        end = n if 0 <= n < len(lines) and lines[n] == LEGACY_REQUEST_END else -1
        if end < 0:
            end = next((i for i in range(len(lines) - 1, -1, -1) if lines[i] == LEGACY_REQUEST_END), -1)
        request = "\n".join(lines if end < 0 else lines[:end])
        rest = text[:hit.start()] + ("" if end < 0 else "\n".join(lines[end + 1:]))
    body, lists, mode = [], {"facts": [], "superseded": []}, "body"
    for line in rest.split("\n"):
        t = line.strip()
        if LEGACY_FACTS_RE.match(t):
            mode = "facts"
            continue
        if LEGACY_SUPERSEDED_RE.match(t):
            mode = "superseded"
            continue
        if mode != "body" and (BULLET_RE.match(line) or t == "" or (re.match(r"^\s", line) and lists[mode])):
            lists[mode].append(line)
            continue
        mode = "body"
        body.append(line)
    return {"request": request, "body": "\n".join(body).strip(), "active": parse_fact_lines(lists["facts"], as_of),
            "superseded": parse_fact_lines(lists["superseded"], as_of), "evicted": []}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("new", help=f"draft brief you just wrote (facts between {FACTS_BEGIN} and {FACTS_END})")
    ap.add_argument("--prev", help="brief you received from your predecessor, if any")
    ap.add_argument("--as-of", help="stamp for new/changed facts (default: current UTC minute)")
    a = ap.parse_args(argv)
    as_of = a.as_of or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    with open(a.new, encoding="utf-8-sig") as fh:
        new_text = fh.read()
    prev_text = None
    if a.prev:
        with open(a.prev, encoding="utf-8-sig") as fh:
            prev_text = fh.read()
    warnings = []
    brief = compose(new_text, prev_text, as_of, warnings)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    for w in warnings:
        print(f"merge_facts: {w}", file=sys.stderr)
    sys.stdout.write(brief)


if __name__ == "__main__":
    main()
