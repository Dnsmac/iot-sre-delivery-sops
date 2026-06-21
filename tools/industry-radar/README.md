# 职业方向雷达（采集工具）

> 生成 **L1 ≤5min 主阅读** + **L2 可选详情**。默认只看 L1。  
> 设计：[`docs/superpowers/specs/2026-05-30-career-direction-radar-design.md`](../../docs/superpowers/specs/2026-05-30-career-direction-radar-design.md)

## 安装（一次性）

```powershell
cd D:\demo\iot-sre-delivery-sops\tools\industry-radar
pip install -r requirements.txt
playwright install chromium
copy config.example.yaml config.yaml   # 可选，无 config 则用 example
```

## 首次登录猎聘

```powershell
python run.py --login liepin
# 浏览器中登录后关闭窗口
```

## 每周（推荐）

```powershell
# 真实采集（需已登录）
python run.py --week 2026-W22

# 或先看流程（样本数据）
python run.py --demo --week 2026-W22
```

**输出：**

| 层 | 路径 |
|----|------|
| **L1（必看）** | `05-Interview-Prep/行业雷达/方向/2026-W22.md` |
| **L2（可选）** | `05-Interview-Prep/行业雷达/详情/2026-W22/` |
| L3 raw | `tools/industry-radar/out/raw/`（gitignore） |

## 仅重新渲染（已有 raw）

```powershell
python run.py --week 2026-W22 --render-only
```

## 注意

- 猎聘页面改版时需改 `config.yaml` → `liepin.selectors`
- `.browser-profile/` 存登录态，**勿提交 git**
- Phase 2：BOSS 采集、Windows 计划任务
