"""
Génère static/css/bootstrap-scoped.min.css : Bootstrap 5 dont TOUTES les règles sont préfixées
par « .hda-bs » -> Bootstrap n'affecte que le contenu entouré de <div class="hda-bs">
et ne casse plus l'en-tête / le pied de page Tailwind du site.
Usage : python outils/scope_bootstrap.py chemin/vers/bootstrap.min.css static/css/bootstrap-scoped.min.css
"""
import re, sys

P = ".hda-bs"

def split_top(s, sep=","):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if ch == sep and depth == 0: out.append(cur); cur = ""
        else: cur += ch
    out.append(cur); return out

def map_selector(sel):
    sel = sel.strip()
    if not sel: return None
    if sel.startswith("[data-bs-theme=dark]") or sel.startswith('[data-bs-theme="dark"]'): return None
    if sel in (":root", "html", "body", "[data-bs-theme=light]", '[data-bs-theme="light"]'): return P
    if sel.startswith("body ") or sel.startswith("html "): return P + sel[4:]
    if sel.startswith("body>") or sel.startswith("body."): return P + sel[4:]
    return f"{P} {sel}"

def blocks(css):
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0: break
        depth, k = 1, j + 1
        while depth and k < n:
            if css[k] == "{": depth += 1
            elif css[k] == "}": depth -= 1
            k += 1
        yield css[i:j].strip(), css[j + 1:k - 1]
        i = k

def scope(css):
    out = []
    for prelude, body in blocks(css):
        if prelude.startswith("@charset") or prelude.startswith("@import"): continue
        if prelude.startswith("@media") or prelude.startswith("@supports"):
            inner = scope(body)
            if inner: out.append(f"{prelude}{{{inner}}}")
        elif prelude.startswith("@"):
            out.append(f"{prelude}{{{body}}}")
        else:
            sels = [m for m in (map_selector(s) for s in split_top(prelude)) if m]
            if sels: out.append(f"{','.join(sels)}{{{body}}}")
    return "".join(out)

if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf8").read()
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    css = scope(src)
    open(sys.argv[2], "w", encoding="utf8").write("/* Bootstrap 5 (MIT) — limité à .hda-bs */" + css)
    print(len(css), "octets")
