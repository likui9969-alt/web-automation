# OrangeHRM 企业级 Web 自动化测试平台

以 OrangeHRM Demo（https://opensource-demo.orangehrmlive.com/  ）为被测系统的测试开发学习项目：
UI 自动化（Playwright）+ API 自动化（Requests）+ 分层测试设计 + CI/CD + Docker。

## 项目状态

> 本节只记录**实际验证过**的事实，禁止虚构测试数量/通过率。进度详见 [MODULE_FEEDBACK.md](MODULE_FEEDBACK.md)。

- [x] M0（已按 M0-lite 收口）：被测系统摸底、C1–C4 硬约束、登录模块 15 项测试点实测、PIM 接口抓包；PIM 测试点由 M4–M6 实践覆盖，Leave/Recruitment 为对应模块开工前置（见 PLAN.md §3 决策记录）
- [x] M1：项目骨架 + 专属 venv + Chromium（镜像下载）+ 裸登录脚本 3 用例，实测 **3 passed**（Builder 35.29s / Reviewer 复跑 29.78s，两次均通过）；git 仓库已初始化（Review P1 已解决）
- [x] M2：Fixture 三层架构（playwright→browser→page）+ 参数化，5 用例实测 **5 passed 36.32s**（较 M1 裸版每例均耗时 -38%）
- [x] M3：POM 重构，定位器集中到 LoginPage，实测 **5 passed 43.24s**（含 Demo 站时段性过载的 flaky 治理：domcontentloaded 等待策略 + 超时 20s 校准，过程留痕）
- [x] M4：API 层（requests 会话客户端 + PIM 接口封装），**5 passed 14.34s**（P2-1 修复后复跑 16.57s）；全量 UI+API **10 passed 65.40s**
- [x] M5：混合造数（数据工厂唯一命名 + API cookie 注入 storage_state 会话复用 + e2e 双向闭环），**全量 12 passed**（Builder 111.68s / Reviewer 104.26s 双绿）；两次真实排障（Save 后竞态 → toast 语义等待；expect 断言 5s 盲区 → 超时校准）
- [x] M6：本地 Docker 部署（OrangeHRM 5.9 + MySQL 8.0，无人值守安装器）+ DB 持久化校验层（pymysql 只读、ohrm_ro 最小权限账号、环境门控 skip）。**本地全量 18 条通过**（本地确定性环境比公网 Demo 快约 4~9 倍，视用例集与时段；同套口径审查方复测 ~7.7 倍）；两次真实排障（解释器错位 → 项目 venv；localhost cookie domain 陷阱 → domain 取 BASE_URL host）。**历经两轮独立复审，P1 全清零后 APPROVED_WITH_FIXES → M6 关闭**（历史：M6 原 APPROVED 曾因审查节由实现方代笔被所有者作废，沉淀为 AGENTS §13.1 制度）
- [x] M7：失败定位体系（失败自动留痕四件套：截图 / Playwright Trace / 浏览器 netlog / API 请求日志；成功零产物；skip/xfail 不误记）。**审查方独立实测闭环 → APPROVED**
- [x] M8：Allure 报告（feature 4 组 / title / severity / attachment 失败截图进报告）。**审查方实测 attachment 链路有效 → APPROVED**
- [x] M9：GitHub Actions 分层 CI（API → UI → e2e，`if: always()` 防吞层）+ flake 度量脚本（ps1 + bash 双平台）+ 浏览器路径代码级根治。**代码/配置层面审查闭环 → APPROVED_WITH_FIXES；唯一剩余 = 真实 Actions 触发（UNVERIFIED，未宣称跑通，需上仓后闭环）**
- [x] M10：测试执行环境 Docker 化（Dockerfile + compose test 服务，容器内全量 18 passed + 1 xfailed 实测；E1–E6 不利条件验证：失败留痕/CWD 兜底/门控识别/零留痕）。**已提交，待独立复审**
- [x] M11：复盘交付物（真实数据统计 / 简历 bullet / 三档项目介绍 / 八问答话术见 docs/）。**按全局收口审查整改中**

> **状态说明**：当前多数模块已 APPROVED；M9 真实 GitHub Actions 触发、M10 独立复审为开放项（见 MODULE_FEEDBACK 状态表与 REVIEW_FEEDBACK）。**公开仓库/简历中不得写"CI 已跑通"**——只能写"workflow 已就绪（真实触发待上仓）"。

## 目录结构与设计理由

```text
├── config/          # 环境差异只允许改配置，不许改测试代码
├── pages/           # POM 层：定位器和页面操作集中，前端改版只改这一层（M3）
├── api/             # 接口语义化封装：用例写 pim.create_employee()，接口变了只改封装层（M4）
├── tests/
│   ├── ui/          # 按层分目录：CI 先跑快的 API 再跑慢的 UI，失败快速反馈
│   ├── api/
│   ├── e2e/         # 区分"纯 UI 验证"和"UI+API 混合业务闭环"（M5）
│   └── db/          # DB 持久化校验：API/UI 操作 → 直查 MySQL 比对（M6，仅本地环境）
├── data/            # 测试数据与代码分离，改数据不改逻辑（M2）
├── utils/           # 数据工厂、DB client 等被多处复用的工具（按需）
├── reports/         # Allure/截图/Trace 产物，已 gitignore（M7/M8）
├── conftest.py      # 全局共享 fixture：浏览器实例、登录态（M2）
├── pytest.ini       # 入口固定 + strict-markers + ui/api/e2e/db 四层 marker
└── requirements.txt # 任何机器一键还原一致环境
```

每个空目录内 `.gitkeep` 注明了激活它的模块——目录是路线图，不是摆设。

## 快速开始

> 实测约束：国内网络下 Playwright 官方 CDN（cdn.playwright.dev）不可达（5 分钟 0% 实测），
> 必须走 npmmirror 镜像；浏览器二进制装在项目内 `.playwright-browsers/`（已 gitignore）。
> 运行时无需手动设置浏览器路径——conftest.py 顶部已 `setdefault` 指向该目录
> （M4 全量运行实测踩坑后的代码级修复，外部显式设置优先）。

```powershell
# 0. 激活项目专属虚拟环境（Python 3.11.9）
.venv\Scripts\Activate.ps1

# 1. 安装依赖
python -m pip install -r requirements.txt

# 2. 下载浏览器二进制（国内镜像，约 300MB，仅首次）
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://cdn.npmmirror.com/binaries/playwright"
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\.playwright-browsers"
playwright install chromium

# 3. 运行
python -m pytest -m ui        # 只跑 UI 层
python -m pytest -m api       # 只跑 API 层（M4 起）
python -m pytest -m e2e       # UI+API 混合闭环（M5 起）
python -m pytest              # 全量

# 4. Allure 报告（M8 起；pytest 运行已自动写 reports/allure-results，
#    HTML 生成需 allure CLI：npm install -g allure-commandline）
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report   # 浏览器打开报告
# 注意：失败用例的现场截图（M7 留痕）会自动作为附件进入报告
```

### 有头模式（想看浏览器实际执行）

默认**无头**（日常回归与 CI 不需要弹窗）。要看着浏览器跑，显式关掉无头：

```powershell
$env:ORANGEHRM_HEADLESS = "false"
python -m pytest -m ui        # 弹出 Chromium 窗口
```

```bash
# Git Bash / Linux / macOS
ORANGEHRM_HEADLESS=false python -m pytest -m ui
```

- 开关只在 `config/settings.py` 一处取值（`HEADLESS`），由 `conftest.py` 的 `browser` fixture 透传给 `chromium.launch()`，**不需要改代码**。
- 解析约定：**只有字符串 `"true"` 表示无头**，其他任何值（`false` / `0` / `no`）都视为有头。注意 `ORANGEHRM_HEADLESS=1` 得到的是**有头**，与直觉相反。
- 有头模式用**完整 chromium**（`chromium-1234`），无头用 `chromium_headless_shell`——`playwright install chromium` 会一并下载，两个组件都要在。
- 排查单个失败用例更实用：`python -m pytest "tests/ui/test_login.py::test_login_valid_credentials"`。
- 代价：有头更慢且会抢焦点，**只在本地排查时开，不要在 CI 里开**。

### 本地 Docker 环境（M6 起，含 DB 校验）

公网 Demo 是共享环境（数据污染、无 DB 权限、公网波动），本地 Docker 副本是确定性的被测系统。
同一套测试代码，**切换只靠环境变量，不改一行代码**：

```powershell
# 1. 拉起本地被测系统（首次含镜像拉取）
docker compose -f docker/docker-compose.yml up -d

# 2. 首次：无人值守安装（配置文件在 docker/cli_install_config.yaml；
#    console 版安装器纯交互式且拒绝 -n，cli_install.php 才是读配置文件
#    的非交互入口——2026-09-15 实测；安装器会自动删除容器内的 yaml）
docker cp docker/cli_install_config.yaml ohrm-app:/var/www/html/installer/
docker exec -w /var/www/html ohrm-app php installer/cli_install.php

# 3. 首次：创建 DB 校验专用只读账号（最小权限在 DB 侧强制，非客户端自律）
docker exec ohrm-db mysql -uroot -proot_password_local -e "CREATE USER 'ohrm_ro'@'%' IDENTIFIED WITH mysql_native_password BY 'ohrm_ro_password_local'; GRANT SELECT ON orangehrm.* TO 'ohrm_ro'@'%'; FLUSH PRIVILEGES;"

# 4. 切换到本地环境跑（凭证为安装配置中的本地专用账号，非公网 Demo）
$env:ORANGEHRM_BASE_URL = "http://localhost:8080"
$env:ORANGEHRM_USERNAME = "Admin"
$env:ORANGEHRM_PASSWORD = "Admin@Local1"
python -m pytest -m db         # DB 持久化校验（仅本地环境，其他环境自动 skip）
python -m pytest              # 全量 18 条
```

不设上述环境变量时默认跑公网 Demo（DB 用例自动 skip）。
MySQL 经宿主机 13306 端口暴露，测试用只读账号 `ohrm_ro` 校验（仅 SELECT，实测 INSERT 被拒）。

**从零重建（一次性破坏性操作，P2-3 实测留痕）**：
compose 为 DB 预置了空库 `orangehrm` 与用户 `ohrm`，而安装器以
`isExistingDatabase: n` 自建库——重建时先 DROP 预置对象保证语义一致，再走首次安装流程：

```powershell
# 1. 删除容器与数据卷（本地数据全部清空，不可恢复）
docker compose -f docker/docker-compose.yml down -v
# 2. 重新拉起
docker compose -f docker/docker-compose.yml up -d
# 3. 等 db healthy 后，DROP 预置空库/用户（on-new-database 语义一致）
docker exec ohrm-db mysql -uroot -proot_password_local -e "DROP DATABASE IF EXISTS orangehrm; DROP USER IF EXISTS 'ohrm'@'%'; FLUSH PRIVILEGES;"
# 4. 之后重复上面第 2-4 步（安装、建只读账号、切环境变量）
```

> **实测口径（2026-09-16，独立复审二轮 P3-1）**：`down -v` 一步按所有者指示
> **未实际执行**；其等效状态（空卷 + 空库）因 Docker Desktop 重启导致数据卷
> 重新初始化而实际出现，重建流程（DROP → 安装 → 建账号 → 核验 171 表）随后
> 全程实测通过。故本流程为「等效路径已验证，`down -v` 命令本身未实跑」。

> 端口已按独立复审 P2-5 绑定 `127.0.0.1`（仅本机可访问）；口令默认值见
> [docker/.env.example](docker/.env.example)，改口令时可复制为 `.env` 覆盖（已被 .gitignore 屏蔽）。
>
> **口令一致性自查（P3-5，改口令后必查）**：`.env`/`.env.example` 的口令必须与
> `docker/cli_install_config.yaml` 一致（compose 只负责容器环境变量，安装器用 yaml 里的
> 口令创建应用账号 —— 不一致则应用登录失败）：
> ```powershell
> Select-String -Path docker\.env.example -Pattern "PASSWORD"   # 期望值
> Select-String -Path docker\cli_install_config.yaml -Pattern "Password:"  # 实际值
> ```

## CI 与 flakes（M9，含 M6 二轮 P2-2 闭环）

### CI 目标环境策略（M11 全局收口审查 P1-2 整改）

CI 目标为**容器路径**（确定性结果）：GitHub hosted runner（ubuntu-latest）**自带
Docker**（正式镜像标准内容），仓库内 M6 被测系统 compose（db+app）与 M10 测试
镜像（Python+Playwright+Chromium）齐备——workflow 起被测系统 → 无人值守安装 →
建只读账号 → 容器内分层跑。**不走公网共享 Demo**（避免环境瞬态打红），
DB 用例因 `BASE_URL=ohrm-app` 被门控识别为本地，**在 CI 中真实执行**。

> ⚠️ **诚实声明**：容器路径 workflow 尚未在真实 GitHub runner 触发（本地 act 网络
> 不可达只验证 job 结构）；**在真实 Actions 跑绿前，不得宣称"CI 已跑通"**，
> 只能写"workflow 已就绪（真实触发待上仓）"。
>
> 历史更正（M11 复审 P1-2）：旧版注释"CI runner 无 Docker daemon"是**错误论据**
> ——runner 自带 Docker；据此曾把 CI 押在公网 Demo（自身最不稳的目标）的决定
> 已废弃。

### flake 度量命令（P2-2「有可复跑命令」，M9 Review P2-2 起双平台）

```powershell
# Windows：同命令 ×N，测公网失败率；结果贴到 MODULE_FEEDBACK「flake 记录」节
.\scripts\flake_measure.ps1 -Runs 3 -Marker ui
# Linux/macOS/CI（与 ps1 等价，输出口径一致；M9 Review P2-2 补齐）
bash scripts/flake_measure.sh -r 3 -m ui
```

任何一次 goto 重试触发都会在 pytest_terminal_summary 输出（M7 P2-1 闭环），
flake 记录须含该计数，区分"flaky 消失"与"被重试救回"。

### 代理策略（M11 全局收口审查 P1-3）

`requests` 默认遵循 `HTTP_PROXY/HTTPS_PROXY` 环境变量（trust_env=True）。开发机
代理未启动时，同一份代码会从全绿变成大范围 `ProxyError`（审查方 2026-09-16 亲身
踩到：11 条 ProxyError + 5 条 TimeoutError，而直连 302 可达）——这类失败曾长期
被误记为"公网瞬态"，归因不可靠。

默认策略：**忽略环境代理直连**（`api/client.py`：`session.trust_env = False`）——
本机/CI/容器行为一致。需要显式走代理时设 `ORANGEHRM_TRUST_ENV=true`。
flake 记录须增加"环境证据"栏（代理状态/网络可达性），失败归因先排除环境再谈代码。

### 容器内跑测试（M10：测试执行环境 Docker 化）

同一套测试代码可在容器内运行（与 M6 的被测系统部署是两回事——这里容器化的是
**测试环境**：Python + Playwright + Chromium 固化为镜像）：

```powershell
# 1. 起被测系统（M6）
docker compose -f docker/docker-compose.yml up -d
# 2. 容器内跑全套（构建测试镜像首次较久，chromium 下载）
docker compose -f docker/docker-compose.yml run --rm test
# 3. 分层跑
docker compose -f docker/docker-compose.yml run --rm test -m api
docker compose -f docker/docker-compose.yml run --rm test -m ui
```

要点（M10 面试）：

- 测试容器与 app/db 同属 compose 网络：`BASE_URL=http://ohrm-app`（compose 服务名
  直连，无需端口映射）、DB 直连 `ohrm-db:3306`（宿主 13306 仅是给人/工具用的映射）
- db 门控把 `ohrm-app` 也识别为本地（conftest），容器内 DB 全套照跑
- 非 root 用户运行：chromium 容器内免 `--no-sandbox`，且更安全
- 留痕/报告经 volume 落宿主 `reports/`，容器跑完宿主直接看截图/Trace/Allure

为什么不能一开始就用 Docker（面试回答）：

- M1 起先本地跑通再容器化——先痛后治：容器化有真实成本（镜像体积、构建时间、
  网络依赖、调试链路加长）
- 只有"环境不一致"成为真痛点（换机器、CI、交付演示）才值得引入，这也是 M10
  才做它的原因

## 被测系统硬约束（项目设计依据）

1. Demo 数据库不可直连 → DB 校验放在本地 Docker 部署环境（M6）
2. Demo 数据多人共享且被重置 → 所有用例自造数据、唯一命名、用后清理
3. 无公开 REST API → 基于抓包的内部接口（`/api/v2/*`，HttpOnly Cookie 会话）测试
4. 公共账号只做只读验证，不改密码、不动公共配置
