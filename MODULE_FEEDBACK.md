# MODULE_FEEDBACK

> 由 Builder 维护。每完成一个模块必须更新本文件，状态机见 AGENTS.md §11。
> 允许状态：IN_PROGRESS / WAITING_FOR_REVIEW / NEEDS_FIX / APPROVED_WITH_FIXES / APPROVED

## 当前状态

| 模块 | 状态 | 更新时间 | 说明 |
|------|------|----------|------|
| M0 需求分析与测试设计 | IN_PROGRESS | 2026-09-15 | 设计输出已完成（PLAN.md、测试金字塔、架构草案）。**登录模块作业已由 Builder 代执行完成**（[homework/M0_登录模块作业.md](homework/M0_登录模块作业.md)，15 条测试点全部实测）。剩余：PIM/Leave/Recruitment 测试点清单。全部完成后转入 WAITING_FOR_REVIEW。 |
| M1 环境搭建 + 裸登录脚本 | APPROVED | 2026-09-15 | Review 85/100 后 P1/P2 全部闭环：P2×2 已修复（README）；P1 git 已解决（见验证记录 2026-09-15 P1 修复行）。**M1 正式关闭，进入 M2** |
| M2 Fixture + 参数化 | APPROVED | 2026-09-15 | Review：**APPROVED_WITH_FIXES → 修复后 APPROVED**。正确项：三层 fixture scope 决策、yield teardown、参数化有 M0 依据、性能归因诚实。P2-1（data/ 承诺未兑现）已修复：参数组外置 `data/credentials.py`，修复后复跑 5 passed in 47.18s。P3×3 记录在 [REVIEW_FEEDBACK.md](REVIEW_FEEDBACK.md) 不阻塞 |

## 验证记录

| 日期 | 模块 | 验证内容 | 实际结果 |
|------|------|----------|----------|
| 2026-09-15 | M0 | 访问 Demo 站确认在线及登录页公开账号 | 已确认：站点在线，登录页展示 `Admin / admin123`（WebFetch 实测） |
| 2026-09-15 | M0 | Demo 数据库直连可行性 | 不可行：托管服务无 MySQL 端口暴露。结论：DB 校验放入 M6 本地部署环境 |
| 2026-09-15 | M0 | 登录模块 15 项测试点实测（浏览器实际操作） | 14 项已验证 + 1 项不测（改公共账号密码，职业道德决策）。关键结论：用户名不区分大小写、不 trim；错误提示统一 "Invalid credentials"（防枚举）；会话 Cookie HttpOnly；登出后服务端会话真实失效；SPA 提交后 1~3 秒重渲染瞬态（flaky 风险实证）。详见作业文件 |
| 2026-09-15 | M0 | PIM 员工列表/搜索接口抓包 | 已捕获：`GET /api/v2/pim/employees?limit=50&offset=0&model=detailed...` 及带 `employeeId=0312` 搜索变体（实测返回 1 条）。登录 POST 细节未捕获（工具限制），待 M4 专项验证 |
| 2026-09-15 | M0 | 共享环境数据污染实证 | 员工记录数 3 分钟内 315→316；列表含大量他人测试数据。证实 C2 约束，M5 数据工厂唯一命名为硬性要求 |
| 2026-09-15 | M0 | 未验证项登记 | 登录 POST 细节、密码重置邮件送达、连续失败锁定机制、超长输入边界、侧边栏点击不导航原因——均已记录于作业文件第六节，禁止在简历/文档中当作已验证事实引用 |
| 2026-09-15 | M1 | 骨架依赖安装 | `python -m pip install -r requirements.txt` 退出码 0。注意：当前 python 指向 `D:\yingyong\hermes\hermes-agent\venv`（宿主机既有虚拟环境），非项目专属 venv——M1 后续考虑建独立 venv，避免污染 |
| 2026-09-15 | M1 | 骨架 pytest 冒烟 | `python -m pytest` 实际输出：pytest 8.4.2，`configfile: pytest.ini` 被正确读取，`testpaths: tests` 生效，collected 0 items，退出码 5（无测试——空骨架预期行为）。playwright 包已安装，**浏览器二进制尚未下载**，M1 首个 UI 测试前需 `playwright install chromium` |
| 2026-09-15 | M1 | 按所有者指定结构扩展完整骨架后复验 | Glob 确认 13 个骨架文件/目录全部就位；`python -m pytest` 再次运行：collected 0 items、退出码 5（预期），结构扩展未破坏收集。README.md 状态节仅含实测事实，未虚构任何测试数量/通过率。另发现 REVIEW_FEEDBACK.md 已由项目所有者放置（空白模板，尚无实际审查） |
| 2026-09-15 | M1 | 项目专属 venv 创建 | `python -m venv .venv` 退出码 0（Python 3.11.9），依赖安装退出码 0。脱离宿主机 hermes venv，环境隔离达成 |
| 2026-09-15 | M1 | Chromium 下载 | 官方 CDN `cdn.playwright.dev` 直连 5 分钟 0%，判断为网络不可达后终止；改用 `PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright` 镜像 + `PLAYWRIGHT_BROWSERS_PATH` 指到项目内 `.playwright-browsers/`，全部组件（Chromium 151.0.7922.34 / FFmpeg / Headless Shell / Winldd）下载成功，退出码 0。**经验沉淀：国内网络环境 Playwright 安装必须配镜像**，已写入 .gitignore 防止二进制入库 |
| 2026-09-15 | M1 | **第一批 UI 测试实际运行** | `pytest -m ui`：**3 passed in 35.29s，退出码 0**。用例：test_login_valid_credentials（断言跳转 /dashboard/index）、test_login_wrong_password（断言 "Invalid credentials" 可见 + URL 未跳转）、test_login_empty_fields（断言 2 处 "Required"）。等待策略全部基于 expect 自动轮询，无任何固定 sleep。35.29s/3 用例即"每用例自建浏览器"的代价，M2 fixture 重构的对照基线 |
| 2026-09-15 | M1 | **Reviewer 独立复跑**（Review 环节） | Reviewer 亲自执行 `pytest -m ui`（非采信 Builder 自述）：**3 passed in 29.78s，退出码 0**。与 Builder 记录的 35.29s 均通过，~18% 时间差佐证"每用例自建浏览器 + 公网 Demo 站"固有波动，基线可信 |
| 2026-09-15 | M1 | P2 修复（Review 后 Builder 执行） | P2-2：README 状态节更新为实测事实（3 passed 双次运行）；P2-1：README 快速开始补国内镜像 + `PLAYWRIGHT_BROWSERS_PATH` 前置条件（PowerShell 可复现步骤）。P1-1（git 安装 + init）待项目所有者配合，未完成，M1 维持 NEEDS_FIX |
| 2026-09-15 | M1 | **P1 修复：git 仓库初始化 + 首次提交** | 实测发现：git 2.55.0 **早已装于 `D:\应用\git\Git`，仅未进 PATH**（winget 亦确认已安装，升级因 UAC 无人值守跳过，不影响使用）。`git init -b main` + 按名 add 15 项 + 首次提交 `c93f61e`，退出码 0，工作区干净（`.venv/`、`.playwright-browsers/`、`chromedriver.exe` 均被 .gitignore 正确排除；chromedriver 为 Selenium 时代残留已补 ignore）。M1 P1 闭环 → APPROVED |
| 2026-09-15 | M2 | **Fixture 重构后实测（含 M1 基线对照）** | `pytest -m ui`：**5 passed in 36.32s，退出码 0**（正向 1 + 错误凭证参数化 3 + 空表单 1）。对照 M1：3 用例 35.29s（均摊 ~11.8s/例）→ 5 用例 36.32s（均摊 ~7.3s/例），**用例数 +67% 总时长持平，单例均摊降 ~38%**。诚实结论：大头仍是公网页面加载与网络往返，浏览器共享只省 ~2s/例——优化收益取决于瓶颈构成（面试点） |
| 2026-09-15 | M2 | 参数化用例生效验证 | pytest 输出显示参数 ID 完整展开：`[Admin-wrongpass123]`、`[nosuchuser-admin123]`、`[nosuchuser-wrongpass123]` 三组独立执行且全部 PASSED——错误用户名场景（M0 实测防枚举：统一 Invalid credentials）首次进入自动化回归 |
| 2026-09-15 | M2 | **Reviewer 独立复跑**（M2 Review 环节） | **5 passed in 45.82s，退出码 0**。第三次运行（35.29/36.32/45.82s 三跑区间），波动 +26% 再证：公网站点时间数据必须看多次运行区间，禁止单点结论 |
| 2026-09-15 | M2 | P2-1 修复后复跑 | 参数组外置 `data/credentials.py`（Python 模块，KISS：3 组元组不值得引入 YAML 解析依赖）+ 删除 data/.gitkeep（占位使命完成）：**5 passed in 47.18s，退出码 0**，用例数与断言零变化——纯数据层重构未破坏行为 |

## M1 自评总结（Builder）

### 交付物

1. 项目骨架 13 个文件/目录（按所有者指定结构，README 记录每个目录的存在理由）
2. 项目专属虚拟环境 `.venv/`（Python 3.11.9），脱离宿主机既有 hermes venv
3. Chromium 二进制（npmmirror 镜像下载至项目内 `.playwright-browsers/`，已 gitignore）
4. 裸登录测试 `tests/ui/test_login_bare.py`：3 用例（LOGIN-01 正向 / LOGIN-02 错误密码 / LOGIN-03 空表单）

### 实测证据

- `pytest -m ui` → 3 passed in 35.29s，退出码 0（见验证记录）
- 骨架冒烟：`pytest` collected 0 items、退出码 5（空骨架预期行为）

### 学到的核心点（面试可讲）

1. **等待策略**：SPA 提交后 1~3 秒重渲染瞬态（M0 实证），用 `expect` 自动轮询断言代替固定 sleep，既稳又不浪费时间
2. **语义定位**：输入框无 label 绑定只能 `get_by_placeholder`，按钮用 `get_by_role`——定位器优先级的实际取舍
3. **环境问题工程化解决**：官方 CDN 不可达 → 镜像 + 项目内 browsers path + gitignore，一次性沉淀为可复现方案
4. **测试分层执行**：`-m ui` / `-m api` marker + `--strict-markers`，拼错 marker 直接报错而非静默跳过

### 故意保留的痛点（M2/M3 的重构动机，非缺陷遗漏）

1. 每用例自建浏览器：3 用例 35.29s，重复 `sync_playwright`/`launch`/`close` 样板 ×3
2. 定位器散落在测试内：前端改版需逐用例修改 → M3 POM
3. 无登录态复用：后续模块（PIM 等）每个用例都要重新走登录流程 → M2 session fixture

### 已知环境约束（未解决，如实登记）

1. 运行 UI 测试时**需设置 `PLAYWRIGHT_BROWSERS_PATH` 指向项目内 `.playwright-browsers/`**（下载时用了自定义路径，运行时同样要指向它；`PLAYWRIGHT_DOWNLOAD_HOST` 仅下载时需要）——README 快速开始未记录此前置条件（Reviewer 确认是否 P2）
2. README "项目状态"节与 M1 实际进度不一致（仍写"待浏览器二进制安装"）——待 M1 Review 后一并更新
