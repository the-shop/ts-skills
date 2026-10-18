import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "skills", "ts-handoff")
sys.path.insert(0, HERE)
import merge_facts as m  # noqa: E402

SCRIPT = os.path.join(HERE, "merge_facts.py")


def f(key, value, as_of="t1"):
    return {"key": key, "value": value, "as_of": as_of}


def fb(*lines):
    return "\n".join([m.FACTS_BEGIN, *lines, m.FACTS_END])


def req_block(text):
    return "\n".join(m.render_request(text))


def brief(*active, sup=()):
    return m.render([f(*a) for a in active], [f(*s) for s in sup])


class MergeFacts(unittest.TestCase):
    def test_parse_keeps_stamp_and_reports_other_lines(self):
        dropped = []
        got = m.parse_fact_lines(["- a: 1", "* b: 2 (as-of: t0)", "- url: http://x:80/a", "prose", "- k:v", "- -: y"], "t3", dropped)
        self.assertEqual(got, [f("a", "1", "t3"), f("b", "2", "t0"), f("url", "http://x:80/a", "t3")])
        self.assertEqual(dropped, ["prose", "- k:v", "- -: y"])

    def test_same_key_supersedes_in_place(self):
        active, sup = m.merge([f("max-retries", "3"), f("db", "pg")], [], [f("Max Retries", "5", "t2"), f("new", "x", "t2")])
        self.assertEqual(active, [f("Max Retries", "5", "t2"), f("db", "pg"), f("new", "x", "t2")])
        self.assertEqual(sup, [f("max-retries", "3")])

    def test_unchanged_keeps_stamp_retired_drops_superseded_cap(self):
        active, sup = m.merge([f("a", "1"), f("b", "2")], [], [f("a", "1", "t2"), f("b", "RETIRED"), f("zz", "RETIRED")])
        self.assertEqual((active, sup), ([f("a", "1")], [f("b", "2")]))
        a, s = [], []
        for i in range(m.MAX_SUPERSEDED + 5):
            a, s = m.merge(a, s, [f("k", str(i))])
        self.assertEqual(a, [f("k", str(m.MAX_SUPERSEDED + 4))])
        self.assertEqual(len(s), m.MAX_SUPERSEDED)

    def test_two_handoffs_spec_change_and_verbatim_request(self):
        req = "Build X.\nRule: keys: kebab-case"
        g1 = m.compose(f"{req_block(req)}\nSTATE: s1\n{fb('- page-size: 50', '- auth: none')}", None, "g1")
        g2 = m.compose(f"STATE: s2\n{fb('- page-size: 100', '- auth: none')}", g1, "g2")
        p = m.parse_brief(g2, "?")
        self.assertEqual((p["request"], p["body"]), (req, "STATE: s2"))
        self.assertEqual(p["active"], [f("page-size", "100", "g2"), f("auth", "none", "g1")])
        self.assertEqual(p["superseded"], [f("page-size", "50", "g1")])

    def test_regression_headings_are_body_and_missing_block_keeps_prev(self):
        prev = brief(("page-size", "50", "g1"))
        for h in ["## Facts (current)", "FACTS (keyed):", "7. FACTS —", "**Key Facts:**", "Facts", "FACTS:"]:
            w = []
            out = m.compose(f"GOAL\n{h}\n- page-size: 100", prev, "g2", w)
            self.assertEqual(m.parse_brief(out, "?")["active"], [f("page-size", "50", "g1")], h)
            self.assertTrue(any(x.startswith("WARNING: no <<<FACTS v1>>> block") for x in w), h)
            self.assertIn(f"{h}\n- page-size: 100", out)

    def test_regression_body_superseded_heading_and_key(self):
        p = m.parse_brief(f"DECISIONS\n### Superseded\n- approach-a: rejected\nNEXT\n{fb('- a: 1', '- superseded-by: PR-14')}", "g")
        self.assertEqual(p["body"], "DECISIONS\n### Superseded\n- approach-a: rejected\nNEXT")
        self.assertEqual(p["active"], [f("a", "1", "g"), f("superseded-by", "PR-14", "g")])

    def test_regression_model_copied_superseded_block_ignored(self):
        prev = brief(("page-size", "100", "g2"), sup=[("page-size", "50", "g1")])
        out = m.compose(f"{fb('- page-size: 100')}\n{m.SUPERSEDED_BEGIN}\n- page-size: 50\n{m.SUPERSEDED_END}", prev, "g3")
        p = m.parse_brief(out, "?")
        self.assertEqual((p["active"], p["superseded"]), ([f("page-size", "100", "g2")], [f("page-size", "50", "g1")]))

    def test_regression_retired_token(self):
        for v in ["RETIRED (as-of: g1)", "`RETIRED`", "**RETIRED**", " RETIRED. ", '"RETIRED"']:
            active, _ = m.merge([f("page-size", "50")], [], m.parse_facts([f"- page-size: {v}"], "g2"))
            self.assertEqual(active, [], v)
        active, _ = m.merge([f("svc-status", "live")], [], [f("svc-status", "Retired", "g2")])
        self.assertEqual(active, [f("svc-status", "Retired", "g2")])

    def test_regression_key_symbols(self):
        out = m.compose(fb("- lang: c++", "- c++: yes", "- c: no", "- !!!: x", "- Deploy_Target: a", "- deploy target: b"), None, "g")
        self.assertEqual(m.parse_brief(out, "?")["active"], [f("lang", "c++", "g"), f("c++", "yes", "g"), f("c", "no", "g"), f("!!!", "x", "g"), f("deploy target", "b", "g")])

    def test_regression_request_block(self):
        req = f"quote:\n{m.REQUEST_END}\nthen more\n{m.FACTS_BEGIN}\n- fake: x\n{m.FACTS_END}"
        out = m.compose(f"{req_block(req)}\n{fb('- a: 1')}", None, "g")
        p = m.parse_brief(out, "?")
        self.assertEqual((p["request"], p["active"]), (req, [f("a", "1", "g")]))
        self.assertNotIn("<<<REQUEST", m.compose(fb("- a: 1"), None, "g"))
        self.assertEqual(m.parse_request(f"<<<REQUEST n_lines=1>>>\nline1\nline2\n{m.REQUEST_END}\nrest"), ("line1\nline2", "rest"))

    def test_regression_prev_request_wins_over_draft(self):
        out = m.compose(f"{req_block('paraphrase')}\n{fb('- a: 1')}", f"{req_block('exact words')}\n{fb('- a: 1')}", "g")
        self.assertEqual(m.parse_brief(out, "?")["request"], "exact words")

    def test_regression_active_cap_and_eviction_traces(self):
        many = [f(f"k{i}", "v") for i in range(m.MAX_ACTIVE)]
        newly = []
        active, _ = m.merge(many, [], [f("k0", "v2"), f("new", "x")], evicted=newly)
        self.assertEqual((len(active), [e["key"] for e in newly]), (m.MAX_ACTIVE, ["k1"]))
        active, _ = m.merge([], [], [f(f"k{i}", "v") for i in range(500)])
        self.assertEqual(len(active), m.MAX_ACTIVE)
        old_sup = [f(f"old{i}", "x", "g0") for i in range(m.MAX_SUPERSEDED)]
        prev = m.render(many, old_sup)
        out = m.compose(fb(*[f"- n{i}: y" for i in range(15)]), prev, "g2")
        p = m.parse_brief(out, "?")
        self.assertEqual(p["superseded"], old_sup)
        self.assertEqual(len(p["evicted"]), m.MAX_EVICTED)
        self.assertEqual(p["evicted"][0], f("k0", "v", "evicted g2, cap 60; set t1"))
        p2 = m.parse_brief(m.compose(fb("- n99: z"), out, "g3"), "?")
        self.assertEqual(p2["evicted"][0], f("k15", "v", "evicted g3, cap 60; set t1"))

    def test_legacy_read_fallback(self):
        legacy = "ORIGINAL USER REQUEST (verbatim, 1 lines):\ndo X\nEND ORIGINAL USER REQUEST\n\nFACTS:\n- a: 1 (as-of: g1)\n\nSUPERSEDED (audit only, NOT current):\n- a: 0 (as-of: g0)\n"
        w = []
        out = m.compose(fb("- b: 2"), legacy, "g2", w)
        p = m.parse_brief(out, "?")
        self.assertEqual((p["request"], p["active"], p["superseded"]), ("do X", [f("a", "1", "g1"), f("b", "2", "g2")], [f("a", "0", "g0")]))
        self.assertEqual(w, ["received brief: no <<<FACTS v1>>> block; read with the legacy heading parser"])

    def test_regression_multiple_facts_blocks(self):
        w = []
        out = m.compose(f"GOAL\n{fb('- page-size: 75', '- a: 1')}\nmiddle\n{fb('- page-size: 100')}", brief(("page-size", "50", "g1")), "g2", w)
        p = m.parse_brief(out, "?")
        self.assertEqual(p["active"], [f("page-size", "100", "g2"), f("a", "1", "g2")])
        self.assertEqual(p["superseded"], [f("page-size", "50", "g1")])
        self.assertEqual(p["body"], "GOAL\nmiddle")
        self.assertNotIn("75", out)
        self.assertEqual(w, ["found 2 <<<FACTS v1>>> blocks; merged in order, last wins per key"])

    def test_regression_body_note_both_sides(self):
        w = []
        out = m.compose("STATE\n- page-size: 100", brief(("page-size", "50", "g1")), "g2", w)
        self.assertTrue(out.startswith(f"{m.BODY_NOTE}\nSTATE"))
        self.assertEqual(len(w), 2)
        succ = m.parse_brief(out, "?", allow_legacy=True)
        self.assertEqual(succ["warnings"], ["body has fact-like lines outside the block (page-size); the <<<FACTS v1>>> block is authoritative"])
        nxt = m.compose(f"{m.BODY_NOTE}\nSTATE2\n{fb('- b: 2')}", out, "g3")
        self.assertEqual(nxt.count(m.BODY_NOTE), 0)

    def test_regression_example_copy_dropped(self):
        with open(os.path.join(HERE, "reference.toon"), encoding="utf-8") as fh:
            row = next(l for l in fh.read().splitlines() if l.strip().startswith("example["))
        example = "\n".join(re.findall(r'"([^"]*)"', row))
        self.assertTrue(example.startswith(m.FACTS_BEGIN) and example.endswith(m.FACTS_END))
        self.assertIn("<key>: <value>", example)
        w = []
        out = m.compose(f"GOAL\n{example}", brief(("a", "1", "g1")), "g2", w)
        self.assertEqual(m.parse_brief(out, "?")["active"], [f("a", "1", "g1")])
        self.assertEqual(w, ['dropped non "key: value" fact line: - <key>: <value>', 'dropped non "key: value" fact line: - <another-key>: <value>'])

    def test_regression_only_exact_placeholders_dropped(self):
        w = []
        out = m.compose(fb("- secret-ref: <redacted>", "- token: <none>", "- env: <unset>", "- <key>: x", "- y: <value>"), brief(("secret-ref", "abc", "g1")), "g2", w)
        self.assertEqual(m.parse_brief(out, "?")["active"], [f("secret-ref", "<redacted>", "g2"), f("token", "<none>", "g2"), f("env", "<unset>", "g2")])
        self.assertEqual(w, ['dropped non "key: value" fact line: - <key>: x', 'dropped non "key: value" fact line: - y: <value>'])

    def test_regression_legacy_body_bullets_warn_with_block(self):
        w = []
        out = m.compose(f"STATE\nFACTS:\n- old-rule: x\n{fb('- a: 1')}", None, "g", w)
        self.assertTrue(out.startswith(m.BODY_NOTE))
        self.assertEqual(w, ["body has fact-like lines outside the block (old-rule); noted in the brief that the FACTS block is authoritative"])
        self.assertEqual(m.parse_brief(out, "?", allow_legacy=True)["warnings"], ["body has fact-like lines outside the block (old-rule); the <<<FACTS v1>>> block is authoritative"])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            prev, new = os.path.join(d, "prev.md"), os.path.join(d, "new.md")
            with open(prev, "w") as fh:
                fh.write(f"{req_block('do it')}\n{fb('- a: 1 (as-of: g1)')}\n")
            with open(new, "w") as fh:
                fh.write(f"STATE: ok\n{fb('- a: 2', 'bad line')}\n")
            r = subprocess.run([sys.executable, "-I", "-B", SCRIPT, new, "--prev", prev, "--as-of", "g2"], capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(r.stdout, f"{req_block('do it')}\nSTATE: ok\n\n{fb('- a: 2 (as-of: g2)')}\n\n{m.SUPERSEDED_LABEL}\n{m.SUPERSEDED_BEGIN}\n- a: 1 (as-of: g1)\n{m.SUPERSEDED_END}\n")
        self.assertIn("dropped", r.stderr)


    def test_regression_request_delimiters_tolerate_whitespace(self):
        text = f"  <<<REQUEST n_lines=1>>>  \nship it\n<<<END REQUEST>>> \nSTATE\n{fb('- a: 1')}\n"
        request, rest = m.parse_request(text)
        self.assertEqual(request, "ship it")
        self.assertNotIn("REQUEST", rest)
        self.assertEqual(m.parse_brief(m.compose(text, None, "g"), "?")["active"], [f("a", "1", "g")])

    def test_regression_bom_draft_and_prev(self):
        with tempfile.TemporaryDirectory() as d:
            prev, new = os.path.join(d, "prev.md"), os.path.join(d, "new.md")
            with open(prev, "w", encoding="utf-8-sig") as fh:
                fh.write(f"{req_block('do it')}\n{fb('- a: 1 (as-of: g1)')}\n")
            with open(new, "w", encoding="utf-8-sig") as fh:
                fh.write(f"{fb('- a: 2')}\n")
            r = subprocess.run([sys.executable, "-I", "-B", SCRIPT, new, "--prev", prev, "--as-of", "g2"], capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(r.stderr, "")
        self.assertTrue(r.stdout.startswith(req_block("do it")))
        self.assertEqual(m.parse_brief(r.stdout, "?")["active"], [f("a", "2", "g2")])

if __name__ == "__main__":
    unittest.main()
