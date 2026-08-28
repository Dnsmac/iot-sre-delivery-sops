# 简历文件说明（只看这里）

> 更新：2026-08-28

## 你要用哪个？

| 用途 | 文件 | 说明 |
|------|------|------|
| **对外投递 / 甲方转正（主用）** | [`投递/骆峰-Java后端-IoT.pdf`](投递/骆峰-Java后端-IoT.pdf) | Boss/猎聘/深开鸿转正 **只用这一份** |
| 改内容 | [`投递/骆峰-Java后端-IoT.html`](投递/骆峰-Java后端-IoT.html) | 改完 HTML 再导出 PDF |
| **外包平台备案（旧）** | `D:\鸿讯文件\java开发 - 骆峰.pdf` | 鸿讯登记用，**已过时，勿当主简历** |
| 历史版本 | [`archive/`](archive/) | 迭代备份，勿投 |

```text
05-Interview-Prep/resume/
├── README.md                 ← 本文件
├── 投递/                     ← ★ 对外只用这里
│   ├── 骆峰-Java后端-IoT.html
│   └── 骆峰-Java后端-IoT.pdf
├── 甲方备案/                 ← 外包/背调专用口径
│   └── README.md
└── archive/                  ← 历史备份，勿投
    └── （旧版 html/pdf）
```

## 两版区别（一句话）

| 版本 | 工作经历写法 |
|------|----------------|
| **投递版** | 2021.03—2024.09 合并为 **一家技术**（简洁，多数岗不背调上家） |
| **甲方备案版** | 拆成 **一家技术 + 谚礼**（与银行流水/劳务协议一致，鸿讯要时用） |

背调若问到 2022 年后主体：口述「同一项目、后期远程、薪资走谚礼」，投递版简历不必写两家。

## 导出 PDF

在项目根目录执行（或浏览器打开 HTML → 打印 → 另存 PDF）：

```powershell
$html = "file:///D:/demo/iot-sre-delivery-sops/05-Interview-Prep/resume/投递/骆峰-Java后端-IoT.html"
$pdf  = "D:\demo\iot-sre-delivery-sops\05-Interview-Prep\resume\投递\骆峰-Java后端-IoT.pdf"
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="$pdf" "$html"
```

## 仓库根目录旧文件

原根目录散落的 `Java开发简历-骆峰-*.html/pdf` 已移入 `archive/`，避免和主版本混淆。
