# -*- coding: utf-8 -*-
"""从全量扫描结果筛出 ≥11 层楼栋，按 社区→村→巷/坊→门牌 排序，附楼栋长联系方式"""
import json, os, csv, re, collections, html as H

SRC = r"C:\Users\kaihong\Desktop\house\原始数据\上下沙楼栋全量.jsonl"
OUT = r"C:\Users\kaihong\Desktop\house"

EXCLUDE = ["电房", "泵房", "泵站", "配电", "变电", "祠堂", "黄公祠", "世祠", "天后宫",
           "广场", "值班室", "管理处", "舞台", "生鲜街市", "商业大街", "中学", "小学",
           "幼儿园", "学校", "京基", "大厦", "市场", "医院", "派出所", "居委会", "党群",
           "工作站", "公园", "公厕", "垃圾", "停车场", "福荣路", "滨河大道", "银行", "酒店"]

CN = "一二三四五六七八九十"
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn2i(s):
    try:
        if s == "十": return 10
        if s.startswith("十"): return 10 + CN.index(s[1]) + 1
        if s.endswith("十"):   return (CN.index(s[0]) + 1) * 10
        return CN.index(s) + 1
    except Exception:
        return 99


def lstrip_com(a):
    return re.sub(r"^(上沙|下沙)社区", "", a)


def village_of(a):
    a = lstrip_com(a)
    if "四十八栋" in a:
        return "上沙四十八栋"
    m = re.search(r"((?:上沙|下沙)?[^0-9一二三四五六七八九十巷号坊]{1,6}?(?:新村路|村路|新村|村))", a)
    return m.group(1) if m else a


def parse2(a):
    a = lstrip_com(a)
    ml = re.search(r"([一二三四五六七八九十]+)巷", a)
    mf = re.search(r"([一二三四五六七八九十]+)坊", a)
    m3 = re.search(r"(\d+)(?:-\d+)?号", a)
    return (cn2i(ml.group(1)) if ml else 999,
            cn2i(mf.group(1)) if mf else 999,
            int(m3.group(1)) if m3 else 999)


VILLAGE_ORDER = {"上沙龙秋村": 1, "上沙椰树村": 2, "上沙塘晏村": 3, "上沙东村": 4,
                 "上沙四十八栋": 5, "上沙村": 6,
                 "下沙村": 11, "东头村路": 12, "下沙新村路": 13}


def norm_tel(t):
    if not t:
        return t
    t = re.sub(r"[./\s]+", "、", t.strip())
    return re.sub(r"、+", "、", t).strip("、")


def uniq_pairs(lst):
    out = []
    for x in lst:
        p = ((x.get("name") or "").strip(), norm_tel(x.get("tel") or ""))
        if p[0] and p not in out:
            out.append(p)
    return out


def nm(lst):
    return "、".join(n for n, t in uniq_pairs(lst)) or "-"


def tl(lst):
    return "、".join(t for n, t in uniq_pairs(lst)) or "-"


def lane_label(r):
    lab = []
    if r["fang"] != 999:
        lab.append(f"{r['fang']}坊")
    if r["lane"] != 999:
        lab.append(f"{r['lane']}巷")
    return "/".join(lab) or "-"


rows = []
for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if not r["x"] or any(k in r["addr"] for k in EXCLUDE) or r["floors"] < 11:
        continue
    r["village"] = village_of(r["addr"])
    r["lane"], r["fang"], r["num"] = parse2(r["addr"])
    rows.append(r)

rows.sort(key=lambda r: (0 if r["community"] == "上沙" else 1,
                         VILLAGE_ORDER.get(r["village"], 50),
                         r["fang"], r["lane"], r["num"], r["addr"]))

# ---------------- CSV ----------------
csv_path = os.path.join(OUT, "上下沙11层以上楼栋-含楼栋长电话-按村巷排序.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["序号", "社区", "村", "巷/坊", "门牌", "层数",
                "楼栋长", "楼栋长手机", "网格员", "网格员手机",
                "经度", "纬度", "楼栋编码", "标准地址"])
    for n, r in enumerate(rows, 1):
        w.writerow([n, r["community"], r["village"], lane_label(r),
                    r["num"] if r["num"] != 999 else "", r["floors"],
                    nm(r["manager"]), tl(r["manager"]),
                    nm(r["gridder"]), tl(r["gridder"]),
                    r["x"], r["y"], r["uid"], r["addr"]])

# ---------------- HTML ----------------
groups = collections.OrderedDict()
for r in rows:
    groups.setdefault((r["community"], r["village"]), []).append(r)

stat = []
for (com, vil), g in groups.items():
    stat.append(f"<tr><td>{com}</td><td>{vil}</td><td>{len(g)}</td>"
                f"<td>{max(x['floors'] for x in g)}</td></tr>")

blocks = []
for (com, vil), g in groups.items():
    trs = []
    for r in g:
        mt, gt = tl(r["manager"]), tl(r["gridder"])
        mgr = f'{nm(r["manager"])}<br><a href="tel:{mt.split("、")[0]}">{mt}</a>'
        grd = f'{nm(r["gridder"])}<br><a href="tel:{gt.split("、")[0]}">{gt}</a>'
        trs.append(
            f"<tr><td class='lk'>{lane_label(r)}</td>"
            f"<td class='no'>{r['num'] if r['num']!=999 else '-'}</td>"
            f"<td class='fl'>{r['floors']}</td><td>{mgr}</td><td>{grd}</td>"
            f"<td class='addr'>{H.escape(r['addr'])}</td></tr>")
    blocks.append(f"""
<section>
 <h2>{com} · {vil} <span class="cnt">{len(g)} 栋</span></h2>
 <table>
  <thead><tr><th>巷/坊</th><th>门牌</th><th>层数</th><th>楼栋长 / 手机</th><th>网格员 / 手机</th><th>标准地址</th></tr></thead>
  <tbody>{''.join(trs)}</tbody>
 </table>
</section>""")

doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>上下沙 ≥11 层楼栋清单（含楼栋长手机 · 按村巷排序）</title>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--line:#e3e3de;--tx:#1c1c1a;--sub:#6b6b66;--hi:#c62828}}
*{{box-sizing:border-box}}
body{{margin:0;padding:22px;background:var(--bg);color:var(--tx);font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
h1{{font-size:20px;margin:0 0 4px}}
.sub{{color:var(--sub);font-size:12px;margin-bottom:16px;line-height:1.7}}
.overview{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:18px;display:inline-block}}
.overview table{{border-collapse:collapse;font-size:13px}}
.overview th,.overview td{{border-bottom:1px solid var(--line);padding:4px 16px 4px 0;text-align:left}}
.tip{{background:#fff8e1;border:1px solid #f0e0b0;border-radius:8px;padding:10px 14px;font-size:12px;color:#7a5c00;margin-bottom:18px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-bottom:16px;overflow:hidden}}
h2{{font-size:15px;margin:0;padding:11px 16px;background:#efefea;border-bottom:1px solid var(--line)}}
.cnt{{float:right;color:var(--sub);font-weight:400;font-size:12px;padding-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{padding:7px 10px;border-bottom:1px solid #f2f2ee;text-align:left;vertical-align:top}}
th{{color:var(--sub);font-weight:500;background:#fafaf7;font-size:12px}}
td.lk{{white-space:nowrap}} td.no{{text-align:right}}
td.fl{{color:var(--hi);font-weight:700;text-align:center}}
td.addr{{color:var(--sub);font-size:12px}}
a{{color:#1565c0;text-decoration:none;white-space:nowrap}}
@media print{{body{{background:#fff;padding:0}}section{{break-inside:avoid;border-color:#ccc}}
 h1{{font-size:16px}} h2{{background:#eee}} .tip{{display:none}}}}
</style></head><body>
<h1>上下沙 ≥11 层楼栋清单</h1>
<div class="sub">
数据源：深圳统一地址库官方接口 · 楼栋长/网格员姓名与手机为官方公示信息（已解密还原）<br>
排序：社区 → 村 → 巷/坊 → 门牌号 · <b>{len(rows)}</b> 栋
</div>
<div class="tip">城中村 ≥11 层基本配电梯，但<b>仍有例外</b>——层数低也可能已加装电梯（如龙秋村 7 巷 4 号仅 8 层，挂牌却写明「独栋电梯房」）。本清单只作初筛，电梯请现场确认。</div>
<div class="overview">
<table><thead><tr><th>社区</th><th>村</th><th>栋数</th><th>最高层</th></tr></thead>
<tbody>{''.join(stat)}</tbody></table>
</div>
{''.join(blocks)}
</body></html>"""

html_path = os.path.join(OUT, "上下沙11层以上楼栋-含楼栋长电话-按村巷排序.html")
open(html_path, "w", encoding="utf-8").write(doc)

print(f"≥11 层 {len(rows)} 栋")
print(f"CSV  -> {csv_path}")
print(f"HTML -> {html_path}")
print("\n=== 分组 ===")
for (com, vil), g in groups.items():
    print(f"  {com} {vil}: {len(g)} 栋（最高 {max(x['floors'] for x in g)} 层）")
