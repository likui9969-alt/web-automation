# MODULE_FEEDBACK

> 由 Builder 维护。每完成一个模块必须更新本文件，状态机见 AGENTS.md §11。
> 允许状态：IN_PROGRESS / WAITING_FOR_REVIEW / NEEDS_FIX / APPROVED_WITH_FIXES / APPROVED

## 当前状态

| 模块 | 状态 | 更新时间 | 说明 |
|------|------|----------|------|
| M0 需求分析与测试设计 | IN_PROGRESS | 2026-09-15 | 设计输出已完成（PLAN.md、测试金字塔、架构草案）。**登录模块作业已由 Builder 代执行完成**（[homework/M0_登录模块作业.md](homework/M0_登录模块作业.md)，15 条测试点全部实测）。剩余：PIM/Leave/Recruitment 测试点清单。全部完成后转入 WAITING_FOR_REVIEW。 |
| M1 环境搭建 + 裸登录脚本 | APPROVED | 2026-09-15 | Review 85/100 后 P1/P2 全部闭环：P2×2 已修复（README）；P1 git 已解决（见验证记录 2026-09-15 P1 修复行）。**M1 正式关闭，进入 M2** |
| M2 Fixture + 参数化 | APPROVED | 2026-09-15 | Review：**APPROVED_WITH_FIXES → 修复后 APPROVED**。正确项：三层 fixture scope 决策、yield teardown、参数化有 M0 依据、性能归因诚实。P2-1（data/ 承诺未兑现）已修复：参数组外置 `data/credentials.py`，修复后复跑 5 passed in 47.18s。P3×3 记录在 [REVIEW_FEEDBACK.md](REVIEW_FEEDBACK.md) 不阻塞 |
| M3 POM | APPROVED | 2026-09-15 | pages/login_page.py 激活 POM：定位器 7→0 处散落、URL/操作语义收编、断言分层取舍有注释。**过程中遭遇真实 flaky**：公网过载致 goto 随机超时（同代码 5P 与 3P+2E 并存），经 wait_until=domcontentloaded + 超时 20s 校准双修复后稳定 5 passed。全程排障记录见验证记录（面试黄金素材） |
| M4 API 层 | APPROVED | 2026-09-15 | **六轮探测证伪链**（表单无 token→JSON 405→UA 无效→Playwright 网络监听抓真相）：登录=Vue 壳 `<auth-login :token>` 提取 + POST /auth/validate；API 真实路径含 /web/index.php 前缀（M0 抓包漏记）。api/client.py + api/pim.py 语义封装，**API 层 5 passed in 14.34s（vs UI 同规模 43.24s，3 倍速差=金字塔实测证据）**。全量 10 passed in 65.40s；conftest setdefault 彻底修复浏览器路径依赖（M1 P2-1 终闭环）。**Review APPROVED_WITH_FIXES → P2-1（PIMApi base_url 一致性）修复后复跑 5 passed 16.57s → APPROVED 终态，M4 关闭** |
| M5 UI+API 混合造数 | APPROVED | 2026-09-15 | 数据工厂（utils/factory.py 唯一命名）+ api/pim.py 增 create/delete/search_by_name（探测实证）+ conftest 会话复用（api_client session 级 + ui_auth_state cookie 注入，收编 M4 P3-1）+ pages/pim_page.py + tests/e2e/ 两条混合闭环用例。**过程中两次真实排障**：①Save 后竞态（前端先发 unique 校验再 POST，~2s 延迟）→ toast 语义等待修复；②全量暴露 expect 断言 5s 盲区（不受 set_default_timeout 影响）→ 断言超时校准。终态 **e2e 2 passed；全量 12 passed**（Builder 111.68s / Reviewer 104.26s 双绿）。**Review APPROVED_WITH_FIXES → P2-1（E2E-02 失败安全清理）修复后复跑 2 passed 31.83s + 残留核验 0 → APPROVED 终态，M5 关闭** |

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
| 2026-09-15 | M3 | POM 重构首跑 | **2 passed + 3 errors（goto 超时 ×3，10s）**。已过的 2 用例证明 POM 逻辑正确，失败全在 setup 的 goto——判定公网过载而非代码问题 |
| 2026-09-15 | M3 | 二跑（确认问题性质） | 1 failed + 4 passed，失败现场页面被带到 www.orangehrm.com（过载跳转痕迹）。两跑不稳定组合：环境故障坐实 |
| 2026-09-15 | M3 | **修复 1：wait_until 策略** | `goto` 默认等 load（全部资源），SPA 只需 DOM ready。改 `wait_until="domcontentloaded"` 后 **5 passed in 35.43s**（正确等待条件优于无脑加大超时，且更快） |
| 2026-09-15 | M3 | **Reviewer 独立复跑（M3 Review）** | 同一代码 Reviewer 跑出 **3 passed + 2 errors**（goto 仍超时）——Builder 5P / Reviewer 3P+2E 并存，坐实时段性过载。Review 价值实证：环境波动只有独立复跑才能暴露 |
| 2026-09-15 | M3 | **修复 2：超时预算校准** | DEFAULT_TIMEOUT 10→20s（注释留痕实测依据：过载时 DOM ready >10s）。环境参数按实测校准，非放宽断言标准（AGENTS §14 合规）。**最终 5 passed in 43.24s，退出码 0** |
| 2026-09-15 | M4 | 探测 v1：表单 POST /auth/validate | 302 回登录页（登录失败）。GET /api/v2/... 返回 404。假设"简单表单提交"被证伪 |
| 2026-09-15 | M4 | 探测 v2：CSRF + XHR header | 登录页 HTML 无 `_csrf_token` 字段；`X-Requested-With` header 未解锁 API（仍 404）。两个假设再证伪 |
| 2026-09-15 | M4 | 探测 v3：JSON POST /auth/login | **405 Method Not Allowed**——SPA JSON 登录假设证伪 |
| 2026-09-15 | M4 | 探测 v4：浏览器 UA | UA 更换无效，404 依旧——WAF 软拦截假设证伪 |
| 2026-09-15 | M4 | 探测 v5：**Playwright 网络监听（决定性）** | 真实登录 POST 抓到：字段为 **`_token`**（Symfony，非 _csrf_token）；API 真实路径为 **`/web/index.php/api/v2/...`**（M0 抓包记录漏 /web/index.php 前缀——404 之谜解开）。教训：四次"合理推测"全错，浏览器网络监听一次定音 |
| 2026-09-15 | M4 | 探测 v6：token 藏匿位置 | 登录页 HTML 壳仅 3467 字节（React SPA 壳），token 在 `<auth-login :token="...">` Vue 组件属性里（HTML 实体编码需 unescape）。全链路实测：提取 token（109 字符）→ POST 302→dashboard → GET employees **200**（meta.total=331）→ 未登录 **401 "Session expired"** → limit=1 返回 1 条 |
| 2026-09-15 | M4 | **API 层实测运行** | `pytest -m api`：**5 passed in 14.34s，退出码 0**（登录成功/错误凭证失败/未登录 401+实测文案/列表结构+关键字段/limit 分页+total 一致性）。对照 UI 层同规模 43.24s——**3 倍速差，测试金字塔的实测证据** |
| 2026-09-15 | M4 | 全量运行（暴露 M1 遗留问题） | `pytest` 不带环境变量：**5 passed（API）+ 5 errors（UI）**——shell 忘设 PLAYWRIGHT_BROWSERS_PATH 则 UI 全挂，M1 Review P2-1 只修了文档没除根。修复：conftest.py 顶部 `os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", 项目内路径)`。**修复后全量 10 passed in 65.40s，零环境变量直接可跑** |
| 2026-09-15 | M4 | Review P2-1 修复（Builder 执行）+ 复跑 | api/pim.py `list_employees` URL 由 `settings.BASE_URL` 改为 `self.client.base_url`（PIMApi 接受 client 参数但 URL 直取全局配置，传自定义 base_url 的 client 时仍打公网——M6 本地 Docker 依赖此设计）。修复后复跑 `pytest -m api`：**5 passed in 16.57s，退出码 0**，用例零变化。M4 → APPROVED 终态 |
| 2026-09-15 | M5 | 探测：员工创建 API | POST /web/index.php/api/v2/pim/employees + JSON body {"firstName","middleName","lastName"} → **200**，data.empNumber 返回主键。M4 建立的 API 风格认知下一次命中（对比 M4 登录探测的六轮证伪） |
| 2026-09-15 | M5 | 探测：员工删除 API 证伪链 | 变体① `?ids[0]=n` → 404 Records Not Found；变体② 路径参数 `/employees/{n}` → 405。**定音：DELETE + JSON body `{"ids":[n]}` → 200 {"data":["544"]}**。附带教训：删除验证时按 employeeId 补零搜索误报"未删"——empNumber（主键 int）与 employeeId（显示编号 str）是两套编号体系，按 lastName 唯一名搜索才确认真删成功 |
| 2026-09-15 | M5 | 探测：搜索参数有效性 | `?name=`（模糊匹配 first/last）**200 有效**；`lastName` 参数 **422 Invalid Parameter**。共享环境再实证：列表 total 331→363（探测时段内他人持续造数），C2 唯一命名必要性 |
| 2026-09-15 | M5 | 探测：cookie 注入会话复用 | API 登录的 `orangehrm` HttpOnly cookie 转换为 Playwright storage_state 格式注入 new_context → 直达 /pim/viewEmployeeList **不跳登录页，h6 显示 "PIM"**。方案可行性确认：e2e 免 UI 登录（快 + 不依赖 SPA 渲染） |
| 2026-09-15 | M5 | 探测：PIM 页 DOM 摸底 | 列表 51 行渲染；搜索框是自动补全 placeholder "Type for hints..."（页面两个，first 为 Employee Name）；空结果显示 "No Records Found"；Add 表单 First/Middle/Last Name placeholder + Cancel/Save 按钮 |
| 2026-09-15 | M5 | e2e 首跑 | **1 error + 1 failed**：①fixture 解包 bug（造数 payload 驼峰字段 vs create_employee 蛇形签名）；②E2E-02 UI 提交后 API 搜不到员工 |
| 2026-09-15 | M5 | **排障：Save 后竞态（Playwright 网络监听诊断）** | Save 点击后监听请求流：前端**先发 employeeId 唯一性校验**（GET core/validation/unique）**再 POST 创建**（点击后 ~2s 才落库，t+3s 出 toast）。立即查 API 必扑空。修复：add_employee 内 `expect("Successfully Saved") toast` 业务语义等待（非 sleep）。诊断过程顺带验证：toast 出现后 API matched 确认 + cleanup 200 |
| 2026-09-15 | M5 | e2e 复跑（修复后） | `pytest -m e2e`：**2 passed in 22.74s，退出码 0**。E2E-01（API 造数→UI 搜索验证）+ E2E-02（UI 添加→API 落库断言→清理）全绿 |
| 2026-09-15 | M5 | **全量首跑（暴露 M3 修复盲区）** | `pytest`：**11 passed + 1 failed in 118.18s**。失败=登录正向用例：expect(to_have_url) 轮询期间 URL=None（dashboard 导航进行中）5s 超时。**根因：expect 断言默认 5s 不受 set_default_timeout(20s) 影响**——M3 超时校准只覆盖操作层，断言层是盲区；本时段公网过载（全量 118s vs M4 65s 佐证）撞上。M5 变更未触碰登录路径，属环境暴露的潜伏问题 |
| 2026-09-15 | M5 | **修复：断言超时校准 + 全量复跑** | expect_logged_in 显式 `timeout=DEFAULT_TIMEOUT*1000`（20s，等待预算校准非放宽断言标准）。全量：**12 passed in 111.68s，退出码 0**（UI 5 + API 5 + e2e 2，公网过载时段全绿） |
| 2026-09-15 | M5 | **Reviewer 独立复跑（M5 Review）** | 全量 `pytest`：**12 passed in 104.26s，退出码 0**（Builder 111.68s，均全绿，~7% 波动属公网正常区间）。判定 APPROVED_WITH_FIXES：P2-1 E2E-02 清理不在失败安全路径（assert 失败时 delete 不执行 → 共享环境残留） |
| 2026-09-15 | M5 | Review P2-1 修复（Builder 执行）+ 复跑 + 清理核验 | E2E-02 清理移入 finally（失败时重新搜索唯一名再删，不依赖 try 内的 matched）。复跑 `pytest -m e2e`：**2 passed in 31.83s，退出码 0**。**清理真实性核验：API 搜索今日 M5 命名（"M5091" 前缀）残留员工数 = 0**——自造自清闭环实证。M5 → APPROVED 终态 |

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
