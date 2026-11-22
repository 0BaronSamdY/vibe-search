import ast, re

path = "app.py"
src = open(path, encoding="utf-8").read()
log = []

old_sel = "vibe_attributes(noise_level,laptop_friendly,romantic,summary)"
new_sel = "vibe_attributes(noise_level,laptop_friendly,romantic,summary,summary_ru,summary_it,summary_en,ai_model,confidence)"
if old_sel in src:
    src = src.replace(old_sel, new_sel); log.append("select: новые колонки")

if "if response.status_code == 400:" not in src:
    pat = re.compile(r"(?P<i>[ ]*)response = requests\.get\(url, headers=headers[^\n]*\)\n")
    def fb(m):
        i = m.group("i")
        return (i + "response = requests.get(url, headers=headers, timeout=15)\n"
                + i + "if response.status_code == 400:\n"
                + i + "    url = url.replace(',summary_ru,summary_it,summary_en,ai_model,confidence', '')\n"
                + i + "    response = requests.get(url, headers=headers, timeout=15)\n")
    src, n = pat.subn(fb, src, count=1)
    if n: log.append("backend: fallback без новых колонок")

anchor = "function t(k){return T[lang][k]||k}"
if "function summaryFor" not in src and anchor in src:
    src = src.replace(anchor, anchor + "\nfunction summaryFor(v){return v['summary_'+lang]||v.summary||t('no_description')}", 1)
    log.append("js: summaryFor()")

if "v.summary||t('no_description')" in src:
    src = src.replace("v.summary||t('no_description')", "summaryFor(v)"); log.append("js: описания по языку")

old_norm = "p.vibe_attributes=[{noise_level:num(v.noise_level),laptop_friendly:num(v.laptop_friendly),romantic:num(v.romantic),summary:v.summary||''}];"
new_norm = "p.vibe_attributes=[Object.assign({},v,{noise_level:num(v.noise_level),laptop_friendly:num(v.laptop_friendly),romantic:num(v.romantic),summary:v.summary||''})];"
if old_norm in src:
    src = src.replace(old_norm, new_norm); log.append("js: поля AI сохраняются")

old_hay = "((p.name||'')+' '+(p.address||'')+' '+(v.summary||'')).toLowerCase()"
new_hay = "((p.name||'')+' '+(p.address||'')+' '+(v.summary||'')+' '+(v.summary_ru||'')+' '+(v.summary_it||'')+' '+(v.summary_en||'')).toLowerCase()"
if old_hay in src:
    src = src.replace(old_hay, new_hay); log.append("js: поиск по всем языкам")

ast.parse(src)
open(path, "w", encoding="utf-8").write(src)
print("✅ Патч применён:" if log else "ℹ️ app.py уже актуален")
for l in log: print("  •", l)
print("✅ Синтаксис Python OK")
