# -*- coding: utf-8 -*-
"""
深圳上下沙城中村民房全量扫描
数据源：深圳统一地址库 https://spatydz.sz.gov.cn/addrdatapc
  1) /standard/search/buildingDetail   -> 标准地址 / 层数 / 坐标
  2) /outerBuilding/queryByBuildingCode -> 楼栋长(姓名+手机) / 网格员(姓名+手机)  [AES-128-ECB 解密]
断点续扫：已完成的 uid 会跳过（读 output jsonl）
"""
import json, urllib.request, urllib.parse, time, base64, os, sys, re
from Crypto.Cipher import AES

BASE = "https://spatydz.sz.gov.cn/addrdatapc"
AK   = "d129375bf07f409a8e5d2ae232712b2a"
KEY  = b"FTKJ.2024" + b"\x00" * 7          # AES-128-ECB

HEAD = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Referer": "https://spatydz.sz.gov.cn/web/",
    "Accept": "application/json, text/plain, */*",
}

OUT_DIR = r"C:\Users\kaihong\Desktop\house\原始数据"
OUT     = os.path.join(OUT_DIR, "上下沙楼栋全量.jsonl")
os.makedirs(OUT_DIR, exist_ok=True)

SLEEP = 0.45

# 社区段实测：008=上沙社区，015=下沙社区
COMMUNITIES = [("440304004008", "上沙"), ("440304004015", "下沙")]
SEG_RANGE   = range(1, 13)          # 段 01~12

# Phase 1 粗扫定界结果（步长 20 实测），上界已加余量
BOUNDS = {
    ("440304004008", 2): 150,  ("440304004008", 3): 310,  ("440304004008", 6): 130,
    ("440304004008", 7): 230,  ("440304004008", 8): 130,  ("440304004008", 9): 30,
    ("440304004008", 10): 110,
    ("440304004015", 1): 30,   ("440304004015", 2): 110,  ("440304004015", 4): 150,
    ("440304004015", 5): 110,  ("440304004015", 6): 110,  ("440304004015", 7): 170,
    ("440304004015", 8): 130,  ("440304004015", 9): 70,
}


def aes_dec(s):
    """AES-128-ECB / Pkcs7，与前端 CryptoJS 等价"""
    if not s or not isinstance(s, str):
        return s
    try:
        raw = base64.b64decode(s)
        if len(raw) % 16:
            return s
        pt = AES.new(KEY, AES.MODE_ECB).decrypt(raw)
        pt = pt[:-pt[-1]] if pt and 1 <= pt[-1] <= 16 else pt
        t = pt.decode("utf-8")
        return t or s
    except Exception:
        return s


def get(path, params, retry=3):
    p = dict(params)
    p["t"] = int(time.time() * 1000)
    url = BASE + path + "?" + urllib.parse.urlencode(p)
    for a in range(retry):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEAD), timeout=20) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            if a == retry - 1:
                return {"_err": str(e)[:90]}
            time.sleep(1.5 + a)
    return {"_err": "unknown"}


def building(uid):
    d = get("/standard/search/buildingDetail", {"buildingId": uid})
    res = d.get("result") or {}
    sa = res.get("standardAddress")
    if not sa:
        return None
    return {
        "addr": sa.replace("广东省深圳市福田区沙头街道", ""),
        "floors": len(res.get("floorList") or []),
        "x": res.get("x"), "y": res.get("y"),
    }


def manager(uid):
    d = get("/outerBuilding/queryByBuildingCode", {"code": uid})
    res = d.get("result") or {}
    bs = res.get("outerBuildingInfoVoList") or []
    gs = res.get("outerGridInfoVoList") or []
    return (
        [{"name": aes_dec(b.get("name")), "tel": aes_dec(b.get("mtel"))} for b in bs],
        [{"name": aes_dec(g.get("fullname")), "tel": aes_dec(g.get("mobilephone"))} for g in gs],
    )


CN = "一二三四五六七八九十"
def cn2i(s):
    try:
        if s == "十": return 10
        if s.startswith("十"): return 10 + CN.index(s[1]) + 1
        if s.endswith("十"):   return (CN.index(s[0]) + 1) * 10
        return CN.index(s) + 1
    except Exception:
        return 99


def parse_addr(a):
    lane = cn2i(re.search(r"([一二三四五六七八九十]+)巷", a).group(1)) if re.search(r"([一二三四五六七八九十]+)巷", a) else 999
    fang = cn2i(re.search(r"([一二三四五六七八九十]+)坊", a).group(1)) if re.search(r"([一二三四五六七八九十]+)坊", a) else 999
    m3 = re.search(r"(\d+)号", a)
    num = int(m3.group(1)) if m3 else 999
    BLK = r"[^0-9一二三四五六七八九十巷号坊栋]"
    m4 = re.search(r"((?:上沙|下沙)" + BLK + r"{0,6}?村)", a)
    if m4:
        vil = m4.group(1)
    else:
        m5 = re.search(r"((?:上沙|下沙)" + BLK + r"*)", a)
        vil = m5.group(1) if m5 else a
    return vil, lane, fang, num


def load_done():
    done = {}
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                r = json.loads(line)
                done[r["uid"]] = r
            except Exception:
                pass
    return done


def emit(rec, fh):
    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    fh.flush()


def main():
    done = load_done()
    print(f"[启动] 已有记录 {len(done)} 栋", flush=True)

    # ---------- Phase 1: 粗扫定界（已缓存则跳过） ----------
    bounds = dict(BOUNDS) if BOUNDS else {}
    if bounds:
        print(f"\n[Phase 1] 使用已缓存定界 {len(bounds)} 段", flush=True)
    else:
        print("\n[Phase 1] 粗扫定界（步长 20，1~800）", flush=True)
        for pfx, name in COMMUNITIES:
            for seg in SEG_RANGE:
                hits = []
                for idx in range(1, 801, 20):
                    uid = f"{pfx}{seg:02d}{idx:05d}"
                    if uid in done:
                        hits.append(idx); continue
                    b = building(uid)
                    if b:
                        hits.append(idx)
                    time.sleep(SLEEP)
                if hits:
                    bounds[(pfx, seg)] = hits[-1] + 25
                    print(f"  {name} 段{seg:02d}: 命中 {len(hits):>2} 点  区间≈{hits[0]}~{hits[-1]}+", flush=True)
                else:
                    print(f"  {name} 段{seg:02d}: 空", flush=True)

    # ---------- Phase 2+3: 细扫 + 楼栋长 ----------
    print("\n[Phase 2] 细扫 + 楼栋长解密", flush=True)
    fh = open(OUT, "a", encoding="utf-8")
    total = 0
    for (pfx, seg), hi in bounds.items():
        name = dict(COMMUNITIES)[pfx]
        got = 0
        for idx in range(1, hi + 1):
            uid = f"{pfx}{seg:02d}{idx:05d}"
            if uid in done:
                got += 1; continue
            b = building(uid)
            time.sleep(SLEEP)
            if not b:
                continue
            mgr, grd = manager(uid)
            time.sleep(SLEEP)
            vil, lane, fang, num = parse_addr(b["addr"])
            rec = {
                "uid": uid, "seg": f"{pfx[-3:]}-{seg:02d}", "community": name,
                "addr": b["addr"], "floors": b["floors"], "x": b["x"], "y": b["y"],
                "village": vil, "lane": lane, "fang": fang, "num": num,
                "manager": mgr, "gridder": grd,
            }
            emit(rec, fh); done[uid] = rec
            got += 1; total += 1
            if total % 50 == 0:
                print(f"  ...{name}段{seg:02d} 已入库{got}栋（累计新增{total}）", flush=True)
        print(f"  ✓ {name} 段{seg:02d} 完成，共 {got} 栋", flush=True)
    fh.close()
    print(f"\n[完成] 全量入库 {len(done)} 栋 -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
