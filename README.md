# OrangeHRM 企业级 Web 自动化测试平台

以 OrangeHRM Demo（https://opensource-demo.orangehrmlive.com/）为被测系统的测试开发学习项目：
UI 自动化（Playwright）+ API 自动化（Requests）+ 分层测试设计 + CI/CD + Docker。

## 项目状态

> 本节只记录**实际验证过**的事实，禁止虚构测试数量/通过率。进度详见 [MODULE_FEEDBACK.md](MODULE_FEEDBACK.md)。

- [x] M0（进行中）：被测系统摸底、登录模块 15 项测试点实测、PIM 接口抓包
- [x] M1：项目骨架 + 专属 venv + Chromium（镜像下载）+ 裸登录脚本 3 用例，实测 **3 passed**（Builder 35.29s / Reviewer 复跑 29.78s，两次均通过）
- [ ] M1 遗留：git 安装 + 仓库初始化（Review P1，待项目所有者配合）
- [ ] M2–M11：Fixture/参数化 → POM → API 层 → 混合造数 → DB 校验 → 失败定位 → Allure → CI → Docker

## 目录结构与设计理由

```text
├── config/          # 环境差异只允许改配置，不许改测试代码
├── pages/           # POM 层：定位器和页面操作集中，前端改版只改这一层（M3）
├── api/             # 接口语义化封装：用例写 pim.create_employee()，接口变了只改封装层（M4）
├── tests/
│   ├── ui/          # 按层分目录：CI 先跑快的 API 再跑慢的 UI，失败快速反馈
│   ├── api/
│   └── e2e/         # 区分"纯 UI 验证"和"UI+API 混合业务闭环"（M5）
├── data/            # 测试数据与代码分离，改数据不改逻辑（M2）
├── utils/           # 数据工厂、DB client 等被多处复用的工具（按需）
├── reports/         # Allure/截图/Trace 产物，已 gitignore（M7/M8）
├── conftest.py      # 全局共享 fixture：浏览器实例、登录态（M2）
├── pytest.ini       # 入口固定 + strict-markers + ui/api 分层 marker
└── requirements.txt # 任何机器一键还原一致环境
```

每个空目录内 `.gitkeep` 注明了激活它的模块——目录是路线图，不是摆设。

## 快速开始

> 实测约束：国内网络下 Playwright 官方 CDN（cdn.playwright.dev）不可达（5 分钟 0% 实测），
> 必须走 npmmirror 镜像；浏览器二进制装在项目内 `.playwright-browsers/`（已 gitignore），
> **运行** UI 测试时同样需要 `PLAYWRIGHT_BROWSERS_PATH` 指向该目录。

```powershell
# 0. 激活项目专属虚拟环境（Python 3.11.9）
.venv\Scripts\Activate.ps1

# 1. 安装依赖
python -m pip install -r requirements.txt

# 2. 下载浏览器二进制（国内镜像，约 300MB，仅首次）
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://cdn.npmmirror.com/binaries/playwright"
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\.playwright-browsers"
playwright install chromium

# 3. 运行（每次新开终端执行 UI 测试前，设置浏览器路径）
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\.playwright-browsers"
python -m pytest -m ui        # 只跑 UI 层
python -m pytest -m api       # 只跑 API 层（M4 起）
python -m pytest              # 全量
```

## 被测系统硬约束（项目设计依据）

1. Demo 数据库不可直连 → DB 校验放在本地 Docker 部署环境（M6）
2. Demo 数据多人共享且被重置 → 所有用例自造数据、唯一命名、用后清理
3. 无公开 REST API → 基于抓包的内部接口（`/api/v2/*`，HttpOnly Cookie 会话）测试
4. 公共账号只做只读验证，不改密码、不动公共配置
