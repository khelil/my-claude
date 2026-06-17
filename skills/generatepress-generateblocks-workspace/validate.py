#!/usr/bin/env python3
"""Grade GenerateBlocks markup outputs against objective validity assertions.
Writes grading.json (fields: text, passed, evidence) into each run dir."""
import json, re, sys, glob, os

ATTR = re.compile(r"<!--\s*wp:([\w/-]+)\s+(\{.*?\})\s*-->", re.DOTALL)
OPEN = re.compile(r"<!--\s*wp:([\w/-]+)(?:\s+\{.*?\})?\s*-->", re.DOTALL)
CLOSE = re.compile(r"<!--\s*/wp:([\w/-]+)\s*-->", re.DOTALL)
DELIM = re.compile(r"<!--.*?-->", re.DOTALL)

def grade(path):
    raw = open(path).read()
    inner = DELIM.sub("", raw)
    res = []

    # A1: produces GB block markup
    gb = re.findall(r"wp:generateblocks/(element|text|media|shape|looper|loop-item|query)", raw)
    res.append(("Produces GenerateBlocks 2.x block markup (element/text/etc.)",
                len(gb) > 0, f"{len(gb)} GB block delimiters found"))

    # A2: balanced delimiters
    opens = OPEN.findall(raw); closes = CLOSE.findall(raw)
    # void media has open+close too; count by name
    res.append(("Block delimiters are balanced (every open has a matching close)",
                len(opens) == len(closes) and len(opens) > 0,
                f"{len(opens)} opens / {len(closes)} closes"))

    # parse all attr JSON
    parsed, parse_ok = [], True
    for name, blob in ATTR.findall(raw):
        try: parsed.append((name, json.loads(blob)))
        except json.JSONDecodeError as e: parse_ok = False
    res.append(("All block-delimiter JSON parses as valid JSON", parse_ok,
                f"{len(parsed)} delimiters parsed"))

    # A4: no literal -- inside delimiters (must be escaped)
    bad = 0
    for m in DELIM.finditer(raw):
        body = m.group(0)[4:-3]  # strip <!-- and -->
        if "--" in body: bad += 1
    res.append(("All `--` inside delimiters escaped as \\u002d\\u002d (valid HTML comments)",
                bad == 0, f"{bad} delimiters contain a raw --"))

    # A3: every styled block has css
    styled = [ (n,a) for n,a in parsed if a.get("styles") ]
    missing_css = [n for n,a in styled if not a.get("css")]
    res.append(("Every styled block carries a precomputed `css` (renders styled on paste)",
                len(missing_css) == 0 and len(styled) > 0,
                f"{len(styled)} styled blocks, {len(missing_css)} missing css"))

    # A5: uniqueId present as class in inner html
    miss_id = []
    for n,a in styled:
        uid = a.get("uniqueId","")
        if uid and uid not in inner: miss_id.append(uid)
    res.append(("Every styled block's uniqueId appears as its inner-HTML class",
                len(miss_id) == 0, f"{len(miss_id)} uniqueIds not found in HTML"))

    # A7: responsive breakpoint
    has_mq = "@media" in raw
    res.append(("Includes a mobile responsive breakpoint (@media)",
                has_mq, "found @media" if has_mq else "no @media"))

    # eval-specific
    ev = path
    if "hero" in ev:
        h1 = len(re.findall(r"<h1[\s>]", inner))
        res.append(("Hero has exactly one H1", h1 == 1, f"{h1} h1 tags"))
        ctas = len(re.findall(r'tagName":"a"', raw)) + len(re.findall(r"<a[\s>]", inner))
        res.append(("Hero has at least two call-to-action links", ctas >= 2, f"~{ctas} anchors"))
    if "feature-grid" in ev:
        grid = "display:grid" in raw or "gridTemplateColumns" in raw or "display\":\"grid" in raw or "display:flex" in raw or "flex" in raw
        res.append(("Uses grid/flex layout for the cards", grid, "layout css present"))
        h3 = len(re.findall(r"<h3[\s>]", inner))
        res.append(("Contains ~4 feature cards (h3 titles)", h3 >= 4, f"{h3} h3 titles"))
    if "pricing" in ev:
        # count price-ish or tier headings
        h3 = len(re.findall(r"<h3[\s>]", inner))
        res.append(("Contains 3 pricing tiers (h3 headings)", h3 >= 3, f"{h3} h3 headings"))
        pop = re.search(r"most popular|most-popular|popular", raw, re.I) is not None
        res.append(("Middle tier flagged as 'most popular'", pop, "popular badge present" if pop else "no popular flag"))

    return [{"text":t,"passed":bool(p),"evidence":e} for t,p,e in res]

for run in sys.argv[1:]:
    outs = [f for f in glob.glob(os.path.join(run,"outputs","*.html")) if not f.endswith(".preview.html")]
    if not outs:
        print("no output in", run); continue
    g = grade(outs[0])
    json.dump({"expectations":g}, open(os.path.join(run,"grading.json"),"w"), indent=2)
    passed = sum(1 for x in g if x["passed"])
    print(f"{run}: {passed}/{len(g)} passed")
