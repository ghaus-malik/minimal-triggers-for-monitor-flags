"""Analysis: what do 1-minimal flagged inputs keep?"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from harness.common import DATA, RESULTS, load_json

R = load_json(os.path.join(DATA, "reductions_A.json"))
res = R["results"]
md = [f"Monitor A (Qwen2.5-7B). Flag threshold P(Yes) > {R['threshold']:.3f} (5% false positives on honest items in the planted-cheat study).", ""]
md.append("| group | n | units before | units kept (mean) | keeps a mechanism line | keeps a patch comment | keeps the message | kept only words (no mechanism line) | kept only the message |")
md.append("|---|---|---|---|---|---|---|---|---|")
summary = {}


def row(name, rs):
    if not rs:
        return
    mech = np.mean(["mechanism" in r["kept_labels"] for r in rs])
    com = np.mean(["patch_comment" in r["kept_labels"] for r in rs])
    msg = np.mean(["message" in r["kept_labels"] for r in rs])
    words_only = np.mean(["mechanism" not in r["kept_labels"] for r in rs])
    msg_only = np.mean([r["kept_labels"] == ["message"] for r in rs])
    size = np.mean([len(r["kept"]) for r in rs])
    before = np.mean([r["n_units"] for r in rs])
    summary[name] = dict(n=len(rs), mech=mech, comment=com, message=msg, words_only=words_only, msg_only=msg_only,
                         kept=size, before=before)
    md.append(f"| {name} | {len(rs)} | {before:.1f} | {size:.1f} | {mech:.2f} | {com:.2f} | {msg:.2f} | {words_only:.2f} | {msg_only:.2f} |")


cheats = [r for r in res if r["kind"] == "cheat"]
for lv in ["explicit", "silent", "misleading"]:
    row(f"cheats, {lv}", [r for r in cheats if r["level"] == lv])
for ct in ["lookup", "special_case", "exit", "always_equal"]:
    row(f"cheats, {ct}", [r for r in cheats if r["ctype"] == ct])
row("all cheats", cheats)
honest = [r for r in res if r["kind"] != "cheat"]
row("flagged honest items (false positives)", honest)
md.append("")
md.append("Examples of minimal flagged inputs (kept units, in order):")
md.append("")
for r in cheats[:0] + [x for x in cheats if x["level"] == "silent"][:4] + [x for x in cheats if x["level"] == "explicit"][:2] + honest[:3]:
    md.append(f"- {r['kind']} / {r['ctype']} / {r['level']}: P(Yes) full {r['full_score']:.2f}, minimal {r['final_score']:.2f}, kept: "
              + " | ".join("`" + t.strip()[:90].replace("|", "/") + "`" for t in r["kept_text"]))
md.append("")
# naturalness-constrained reductions (code must parse and define the function)
sp = os.path.join(DATA, "reductions_syntax_A.json")
if os.path.exists(sp):
    R2 = load_json(sp)
    res2 = R2["results"]
    md.append("### With a naturalness constraint (kept code must parse and define the task function)")
    md.append("")
    md.append("| group | n | units before | units kept (mean) | keeps a mechanism line | keeps a patch comment | keeps the message | kept only words (no mechanism line) | kept only the message |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    c2 = [r for r in res2 if r["kind"] == "cheat"]
    for lv in ["explicit", "silent", "misleading"]:
        row(f"syntax: cheats, {lv}", [r for r in c2 if r["level"] == lv])
    row("syntax: all cheats", c2)
    row("syntax: flagged honest items", [r for r in res2 if r["kind"] != "cheat"])
    emp = np.array([r["empty_score"] for r in res2])
    md.append("")
    md.append(f"Control: the empty input (task only, no code, no message) gets P(Yes) = {emp.mean():.2f} on average, "
              f"above the flag threshold in {np.mean(emp > R2['threshold']):.0%} of items.")
    summary["empty_input_mean"] = float(emp.mean())
    summary["empty_input_flagged"] = float(np.mean(emp > R2["threshold"]))
    md.append("")
    md.append("Examples (syntax-constrained):")
    md.append("")
    for r in [x for x in c2 if x["level"] == "silent"][:4] + [x for x in c2 if x["level"] == "misleading"][:3] + [x for x in res2 if x["kind"] != "cheat"][:2]:
        md.append(f"- {r['kind']} / {r['ctype']} / {r['level']}: kept "
                  + " | ".join("`" + t.strip()[:90].replace("|", "/") + "`" for t in r["kept_text"]))
    md.append("")
# word-only probes
for which in ["A", "B"]:
    path = os.path.join(DATA, f"probes_{which}.json")
    if not os.path.exists(path):
        continue
    P = load_json(path)
    md.append(f"Word-only probes on honest, correct code, monitor {which} (threshold {P['threshold']:.3f}):")
    md.append("")
    md.append("| probe | n | flagged | mean P(Yes) |")
    md.append("|---|---|---|---|")
    summary[f"probes_{which}"] = {}
    for probe in ["plain", "cheat comment only", "cheat message only", "comment and message"]:
        s = np.array([x["p_yes"] for x in P["rows"] if x["probe"] == probe])
        summary[f"probes_{which}"][probe] = dict(n=len(s), flagged=float(np.mean(s > P["threshold"])), mean=float(np.mean(s)))
        md.append(f"| {probe} | {len(s)} | {np.mean(s > P['threshold']):.2f} | {np.mean(s):.2f} |")
    md.append("")
with open(os.path.join(RESULTS, "results.json"), "w") as f:
    json.dump(summary, f, indent=1, default=float)
with open(os.path.join(RESULTS, "tables.md"), "w") as f:
    f.write("\n".join(md))
print("\n".join(md))
