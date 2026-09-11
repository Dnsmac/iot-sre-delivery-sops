# -*- coding: utf-8 -*-
"""把扫描结果生成 按 村→巷/坊→门牌 排序的 CSV + 可打印 HTML"""
import json, os, csv, re, collections, html as H

SRC = r"C:\Users\kaihong\Desktop\house\原始数据\上下沙楼栋全量.jsonl"
OUT = r"C:\Users\kaihong\Desktop\house"

# 明显不是住宅的（电房/祠堂/广场/学校/商城/管理设施），出清单时排除
EXCLUDE = ["电房", "泵房", "泵站", "配电", "变电", "祠堂", "黄公祠", "世祠", "天后宫",
           "广场", "值班室", "管理处", "舞台", "生鲜街市", "商业大街", "中学", "小学",
           "幼儿园", "学校", "京基", "大厦", "市场", "医院", "派出所", "居委会", "党群",
           "工作站", "公园", "公厕", "垃圾", "停车场", "福荣路", "滨河大道", "银行", "酒店"]

CN = "一二三四五六七八九十"


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
    if m:
        return m.group(1)
    m = re.search(r"((?:上沙|下沙)[^0-9一二三四五六七八九十巷号坊栋]*)", a)
    return m.group(1) if m else a


def parse2(a):
    a = lstrip_com(a)
    lane = cn2i(re.search(r"([一二三四五六七八九十]+)巷", a).group(1)) if re.search(r"([一二三四五六七八九十]+)巷", a) else 999
    fang = cn2i(re.search(r"([一二三四五六七八九十]+)坊", a).group(1)) if re.search(r"([一二三四五六七八九十]+)坊", a) else 999
    m3 = re.search(r"(\d+)(?:-\d+)?号", a)
    num = int(m3.group(1)) if m3 else 999
    return lane, fang, num


# 村间顺序（人工指定，符合实地认知）
VILLAGE_ORDER = {
    "上沙龙秋村": 1, "上沙椰树村": 2, "上沙塘晏村": 3, "上沙东村": 4,
    "上沙四十八栋": 5, "上沙村": 6,
    "下沙村": 11, "东头村路": 12, "下沙新村路": 13, "下沙新村": 14,
}

rows = []
for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if not r["x"] or any(k in r["addr"] for k in EXCLUDE):
        continue
    r["village"] = village_of(r["addr"])
    r["lane"], r["fang"], r["num"] = parse2(r["addr"])
    rows.append(r)


def sort_key(r):
    return (0 if r["community"] == "上沙" else 1,
            VILLAGE_ORDER.get(r["village"], 50),
            r["fang"], r["lane"], r["num"], r["addr"])


res = sorted(rows, key=sort_key)


def norm_tel(t):
    if not t:
        return t
    t = t.strip()
    t = re.sub(r"[./\s]+", "、", t)
    t = re.sub(r"、+", "、", t).strip("、")
    return t


def uniq_pairs(lst, nk, tk):
    out = []
    for x in lst:
        p = ((x.get(nk) or "").strip(), norm_tel(x.get(tk) or ""))
        if p[0] and p not in out:
            out.append(p)
    return out


def names(lst, nk="name", tk="tel"):
    return "、".join(n for n, t in uniq_pairs(lst, nk, tk)) or "-"


def tels(lst, nk="name", tk="tel"):
    return "、".join(t for n, t in uniq_pairs(lst, nk, tk)) or "-"


def mgr_names(r): return names(r["manager"])
def mgr_tels(r):  return tels(r["manager"])
def grd_names(r): return names(r["gridder"], "name", "tel")
def grd_tels(r):  return tels(r["gridder"], "name", "tel")


def lane_label(r):
    lab = []
    if r["fang"] != 999:
        lab.append(f"{r['fang']}坊")
    if r["lane"] != 999:
        lab.append(f"{r['lane']}巷")
    return "/".join(lab) or "-"


# ---------------- CSV ----------------
csv_path = os.path.join(OUT, "上下沙民房楼栋清单-按村巷排序.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["序号", "社区", "村", "巷/坊", "门牌", "层数", "电梯推测",
                "楼栋长", "楼栋长电话", "网格员", "网格员电话",
                "经度", "纬度", "楼栋编码", "标准地址"])
    for n, r in enumerate(res, 1):
        fl = r["floors"]
        guess = "≥11层·基本有电梯" if fl >= 11 else ("8-10层·需现场确认" if fl >= 8 else "低层·一般无电梯")
        w.writerow([n, r["community"], r["village"], lane_label(r),
                    r["num"] if r["num"] != 999 else "",
                    fl, guess,
                    mgr_names(r), mgr_tels(r),
                    grd_names(r), grd_tels(r),
                    r["x"], r["y"], r["uid"], r["addr"]])

# ---------------- HTML ----------------
groups = collections.OrderedDict()
for r in res:
    groups.setdefault((r["community"], r["village"]), []).append(r)

stat = []
for (com, vil), g in groups.items():
    hi = sum(1 for x in g if x["floors"] >= 11)
    stat.append(f"<tr><td>{com}</td><td>{vil}</td><td>{len(g)}</td><td>{hi}</td><td>{sum(1 for x in g if x['floors']>=8)}</td></tr>")

blocks = []
for (com, vil), g in groups.items():
    trs = []
    for r in g:
        fl = r["floors"]
        cls = "hi" if fl >= 11 else ("mid" if fl >= 8 else "")
        mt, gt = mgr_tels(r), grd_tels(r)
        mgr = f'{mgr_names(r)}<br><a href="tel:{mt.split("、")[0]}">{mt}</a>'
        grd = f'{grd_names(r)}<br><a href="tel:{gt.split("、")[0]}">{gt}</a>'
        trs.append(
            f"<tr class='{cls}'><td class='lk'>{lane_label(r)}</td>"
            f"<td class='no'>{r['num'] if r['num']!=999 else '-'}</td>"
            f"<td class='fl'>{fl}</td><td>{mgr}</td><td>{grd}</td>"
            f"<td class='addr'>{H.escape(r['addr'])}</td></tr>")
    blocks.append(f"""
<section>
  <h2>{com} · {vil} <span class="cnt">{len(g)} 栋</span></h2>
  <table>
   <thead><tr><th>巷/坊</th><th>门牌</th><th>层数</th><th>楼栋长 / 电话</th><th>网格员 / 电话</th><th>标准地址</th></tr></thead>
   <tbody>{''.join(trs)}</tbody>
  </table>
</section>""")

doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>深圳上下沙民房楼栋清单（按村巷排序 · 含楼栋长联系方式）</title>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--line:#e3e3de;--tx:#1c1c1a;--sub:#6b6b66;--hi:#c62828;--mid:#b8860b}}
*{{box-sizing:border-box}}
body{{margin:0;padding:22px;background:var(--bg);color:var(--tx);font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
h1{{font-size:20px;margin:0 0 4px}}
.sub{{color:var(--sub);font-size:12px;margin-bottom:16px;line-height:1.7}}
.overview{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:18px;display:inline-block}}
.overview table{{border-collapse:collapse;font-size:13px}}
.overview th,.overview td{{border-bottom:1px solid var(--line);padding:4px 16px 4px 0;text-align:left}}
.legend{{margin:10px 0 18px;font-size:12px;color:var(--sub)}}
.legend b.hi{{color:var(--hi)}} .legend b.mid{{color:var(--mid)}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-bottom:16px;overflow:hidden}}
h2{{font-size:15px;margin:0;padding:11px 16px;background:#efefea;border-bottom:1px solid var(--line)}}
.cnt{{float:right;color:var(--sub);font-weight:400;font-size:12px;padding-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{padding:6px 10px;border-bottom:1px solid #f2f2ee;text-align:left;vertical-align:top}}
th{{color:var(--sub);font-weight:500;background:#fafaf7;font-size:12px;position:sticky;top:0}}
td.lk{{white-space:nowrap;color:#333}} td.no{{text-align:right;color:#333}}
tr.hi td.fl{{color:var(--hi);font-weight:700}}
tr.mid td.fl{{color:var(--mid);font-weight:600}}
td.addr{{color:var(--sub);font-size:12px}}
a{{color:#1565c0;text-decoration:none;white-space:nowrap}}
@media print{{body{{background:#fff;padding:0}}section{{break-inside:avoid;border-color:#ccc}}
 h1{{font-size:16px}} h2{{background:#eee}} th{{position:static}}}}
</style></head><body>
<h1>深圳上下沙民房楼栋清单</h1>
<div class="sub">
数据源：深圳统一地址库（spatydz.sz.gov.cn）官方楼栋级接口 · 楼栋长/网格员姓名与手机为官方公示信息，经 AES 解密还原<br>
排序：社区 → 村 → 巷/坊 → 门牌号（<b>不按楼层排序</b>）· 民房合计 <b>{len(res)}</b> 栋
</div>
<div class="overview">
<table><thead><tr><th>社区</th><th>村</th><th>楼栋数</th><th>≥11 层</th><th>≥8 层</th></tr></thead>
<tbody>{''.join(stat)}</tbody></table>
</div>
<div class="legend">层数图例：<b class="hi">红色 = ≥11 层</b>（城中村这一高度基本配电梯）· <b class="mid">橙色 = 8–10 层</b>（需现场确认，部分已加装）· 黑色 = 8 层以下（一般无电梯，个别已加装）</div>
{''.join(blocks)}
</body></html>"""

html_path = os.path.join(OUT, "上下沙民房楼栋清单-按村巷排序.html")
open(html_path, "w", encoding="utf-8").write(doc)

print(f"民房 {len(res)} 栋")
print(f"CSV  -> {csv_path}")
print(f"HTML -> {html_path}")
print("\n=== 分组 ===")
for (com, vil), g in groups.items():
    hi = sum(1 for x in g if x["floors"] >= 11)
    print(f"  {com} {vil}: {len(g)} 栋（≥11层 {hi}）")
