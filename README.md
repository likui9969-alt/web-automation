# OrangeHRM 企业级 Web 自动化测试平台

以 OrangeHRM Demo（https://opensource-demo.orangehrmlive.com/）为被测系统的测试开发学习项目：
UI 自动化（Playwright）+ API 自动化（Requests）+ 分层测试设计 + CI/CD + Docker。

## 项目状态

> 本节只记录**实际验证过**的事实，禁止虚构测试数量/通过率。进度详见 [MODULE_FEEDBACK.md](MODULE_FEEDBACK.md)。

- [x] M0（已按 M0-lite 收口）：被测系统摸底、C1–C4 硬约束、登录模块 15 项测试点实测、PIM 接口抓包；PIM 测试点由 M4–M6 实践覆盖，Leave/Recruitment 为对应模块开工前置（见 PLAN.md §3 决策记录）
- [x] M1：项目骨架 + 专属 venv + Chromium（镜像下载）+ 裸登录脚本 3 用例，实测 **3 passed**（Builder 35.29s / Reviewer 复跑 29.78s，两次均通过）；git 仓库已初始化（Review P1 已解决）
- [x] M2：Fixture 三层架构（playwright→browser→page）+ 参数化，5 用例实测 **5 passed 36.32s**（较 M1 裸版每例均耗时 -38%）
- [x] M3：POM 重构，定位器集中到 LoginPage，实测 **5 passed 43.24s**（含 Demo 站时段性过载的 flaky 治理：domcontentloaded 等待策略 + 超时 20s 校准，过程留痕）
- [x] M4：API 层（requests 会话客户端 + PIM 接口封装），**5 passed 14.34s**（P2-1 修复后复跑 16.57s）；全量 UI+API **10 passed 65.40s**
- [x] M5：混合造数（数据工厂唯一命名 + API cookie 注入 storage_state 会话复用 + e2e 双向闭环），**全量 12 passed**（Builder 111.68s / Reviewer 104.26s 双绿）；两次真实排障（Save 后竞态 → toast 语义等待；expect 断言 5s 盲区 → 超时校准）
- [x] M6：本地 Docker 部署（OrangeHRM 5.9 + MySQL 8.0，无人值守安装器）+ DB 持久化校验层（pymysql 只读、ohrm_ro 最小权限账号、环境门控 skip）。**本地全量 18 条通过**（独立复审实测极差区间约 4~9 倍于公网同套，具体视用例集与时段；本地确定性 5/5）；两次真实排障（解释器错位 → 项目 venv；localhost cookie domain 陷阱 → domain 取 BASE_URL host）。**状态：NEEDS_FIX（独立复审 P1-1/P1-2/P1-3，M6 原 APPROVED 因审查节由实现方代笔被所有者裁定作废；修复在途，见 MODULE_FEEDBACK）**
- [ ] M7–M11：失败定位 → Allure → CI → 模拟环境

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
```

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

**从零重建（一次性破坏性操作，独立复审 P2-3 实测留痕）**：
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

> 端口已按独立复审 P2-5 绑定 `127.0.0.1`（仅本机可访问）；口令默认值见
> [docker/.env.example](docker/.env.example)，改口令时可复制为 `.env` 覆盖（已被 .gitignore 屏蔽）。

## 被测系统硬约束（项目设计依据）

1. Demo 数据库不可直连 → DB 校验放在本地 Docker 部署环境（M6）
2. Demo 数据多人共享且被重置 → 所有用例自造数据、唯一命名、用后清理
3. 无公开 REST API → 基于抓包的内部接口（`/api/v2/*`，HttpOnly Cookie 会话）测试
4. 公共账号只做只读验证，不改密码、不动公共配置
