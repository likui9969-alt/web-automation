# OrangeHRM 企业级 Web 自动化测试平台 — 总体实施计划

> 本文件是项目的唯一计划来源（Single Source of Truth）。
> 每个模块的执行流程、状态流转、禁止事项以 [AGENTS.md](AGENTS.md) 为准。
> 最近更新：2026-09-15

---

## 0. 项目背景与硬约束

被测系统：OrangeHRM Demo — https://opensource-demo.orangehrmlive.com/ （账号 `Admin / admin123`，页面公开展示）

已实际确认的硬约束（2026-09-15 摸底）：

| # | 约束 | 对策 |
|---|------|------|
| C1 | Demo 数据库不可直连（托管服务） | M6 用 Docker 本地部署 OrangeHRM 开源版做 DB 校验，明确标注「本地学习环境 ≠ Demo 线上环境」 |
| C2 | Demo 数据多人共享 + 定期重置 | 所有用例自带数据（数据工厂 + 唯一命名 + 用完清理），禁止断言固定数据 |
| C3 | 无文档化公开 REST API（前端走内部接口，cookie 会话鉴权） | 抓包 → requests 重放；面试中如实说明是「基于抓包的内部接口测试」 |
| C4 | Demo 部分操作受限（如改 admin 密码、删预置数据） | 每个测试点以实际验证为准，未验证一律标注「未验证」 |

---

## 1. 技术栈引入顺序及理由

```
Python → Pytest → Playwright → POM → Requests → MySQL(本地) → 失败定位 → Allure → GitHub Actions → Docker
```

原则：**每引入一个工具，都必须先有「没有它会痛」的真实动机**。链路先跑通，最后才容器化。

---

## 2. 模块总览

| 模块 | 主题 | 核心技术 | 前置依赖 | 验证方式 |
|------|------|----------|----------|----------|
| M0 | 需求分析 + 测试范围 + 架构 | 测试金字塔、测试点设计、抓包 | — | 作业评审 |
| M1 | 环境搭建 + 裸登录脚本 | Playwright、Locator、自动等待 | M0 | pytest 实际运行 |
| M2 | Fixture + 参数化重构 | pytest fixture、parametrize、数据分离 | M1 | pytest 实际运行 |
| M3 | POM 重构 | Page Object Model | M2 | pytest 实际运行 |
| M4 | API 测试层 | requests.Session、cookie 鉴权、断言设计 | M0 抓包成果 | pytest 实际运行 |
| M5 | UI+API 混合造数 | 数据工厂、测试独立性、清理策略 | M3 + M4 | pytest 实际运行 |
| M6 | 本地部署 + 数据库校验 | Docker、MySQL、pymysql | M5 | 实际查库比对 |
| M7 | 失败定位体系 | 截图、Trace、日志、请求响应留痕 | M5 | 故意制造失败并验证留痕 |
| M8 | Allure 报告 | allure-pytest、step/severity/attachment | M7 | 生成并检查报告 |
| M9 | GitHub Actions CI | workflow、分层执行、artifact | M8 | push 实际触发 |
| M10 | Docker 化 | Dockerfile、环境一致性 | M9 | 容器内实际跑通 |
| M11 | 复盘 + 简历/面试材料 | 真实数据统计 | M1–M10 | 口头演练 |

每个模块之间是 **Review 门禁**：未经 REVIEW_FEEDBACK.md 判定 APPROVED，禁止进入下一模块。

---

## 3. 各模块详细计划

### M0 需求分析与测试设计（当前模块 · IN_PROGRESS）

- **为什么**：测试开发的第一步是分析被测系统，不是写脚本。
- **已完成**：被测系统摸底、四条硬约束、登录模块测试点示范、测试金字塔、架构草案、本计划。
- **待完成（用户作业）**：
  1. PIM / Leave / Recruitment 三模块测试点清单，每模块 ≥8 条，含编号/测试点/类型/建议层级/优先级，且每条在 Demo 上实际操作验证过；
  2. 抓包记录 ×2：登录请求、PIM 搜索员工请求（方法/URL/请求头/请求体/响应顶层结构）；
  3. 思考题 ×3（全 UI 化的弊端、共享环境数据稳定性、UI 断言 vs API 断言的本质区别）。
- **交付物**：PLAN.md、测试点清单、抓包记录。
- **DoD**：作业提交 → Reviewer 独立评审通过 → 用户能讲清分层理由。

### M1 环境搭建 + 裸登录脚本

- **为什么**：先痛后治。故意不用 Fixture/POM 写能跑的登录脚本，亲手制造重复与脆弱，为 M2/M3 的重构提供真实动机。
- **任务**：最小骨架（config/、tests/、conftest.py、pytest.ini、requirements.txt）；安装 Playwright；登录正向 + 反向裸脚本。
- **知识点**：Playwright 同步 API、`get_by_role/label/text`、自动等待机制。
- **验证**：pytest 实际跑通并记录输出。
- **面试主题**：Playwright 与 Selenium 等待机制差异；定位策略优先级。

### M2 Fixture + 参数化重构

- **为什么**：M1 的裸脚本里每个用例重复建浏览器/重复登录 → Fixture 解决；错误密码 4 种组合写成 4 个函数是复制粘贴 → parametrize 解决。
- **任务**：抽 browser/page fixture（讨论 scope）；登录负向用例参数化；测试数据移入 data/。
- **知识点**：fixture scope（function/class/module/session）、yield teardown、数据与逻辑分离。
- **面试主题**：Fixture vs setup/teardown；scope 怎么选；为什么参数化优于复制。

### M3 POM 重构

- **为什么**：定位器散落在测试里，页面一改全挂 → POM 集中维护；测试只表达业务步骤。
- **任务**：LoginPage、PimPage、BasePage；重构 M1/M2 用例。
- **知识点**：POM 解决的真正问题是「变更隔离」，不是「看起来专业」；什么场景不该用 POM。
- **面试主题**：POM 本质与代价。

### M4 API 测试层

- **为什么**：内部接口抓包重放，快、稳、断言精确；同时为 M5 的 API 造数打基础。
- **任务**：api/ 封装（Session + cookie 鉴权）；登录接口、PIM 查询/添加接口用例；状态码 + JSON 结构断言；异常入参负向用例。
- **知识点**：requests.Session、Header/Cookie、断言设计（状态码 ≠ 业务正确）。
- **面试主题**：API 测试怎么设计；UI 断言与 API 断言的差异。

### M5 UI + API 混合：测试数据策略

- **为什么**：UI 造数慢且脆；「API 造数 + UI 验证」是工业界标准做法；Demo 共享环境必须自带数据。
- **任务**：数据工厂（唯一命名）；API 造数 → UI 验证闭环；用例结束清理。
- **面试主题**：测试数据管理；测试独立性；flaky test 的主要来源。

### M6 本地部署 OrangeHRM + 数据库校验

- **为什么**：C1 约束下，DB 校验只能在自部署环境真实执行。
- **任务**：Docker 部署 OrangeHRM + MySQL；pymysql 校验「添加员工」落库结果；数据一致性断言。
- **面试主题**：为什么「页面显示成功」不等于成功；DB 校验该放在什么时机。

### M7 失败定位体系

- **为什么**：自动化测试一半的价值在失败时能否 5 分钟内定位。
- **任务**：失败自动截图、Playwright Trace、日志、API 请求/响应留痕（conftest hook 实现）。
- **验证方式**：故意制造一个失败用例，走一遍「失败 → 看报告 → 看截图/Trace → 定位」全流程。
- **面试主题**：flaky 怎么排查；Trace 怎么用。

### M8 Allure 报告

- **任务**：集成 allure-pytest；step/title/severity/attachment 落地。
- **面试主题**：报告在真实团队中的作用（不是"有报告"，而是"让不写代码的人看得懂质量现状"）。

### M9 GitHub Actions CI

- **任务**：push → 安装依赖 → 先跑 API（快、先反馈）再跑 UI → 上传 Allure 结果 artifact；测试失败则 Pipeline 红。
- **面试主题**：为什么自动化必须进 CI；测试框架与 CI/CD 的关系。

### M10 Docker 化

- **任务**：编写 Dockerfile 在容器内跑全套测试（目标为本地部署的被测系统）；讨论 Demo vs 本地两套目标环境的取舍。
- **面试主题**：Docker 解决什么问题（环境一致性）；为什么不能一开始就用 Docker。

### M11 复盘 + 简历/面试材料

- **任务**：基于**真实运行记录**统计用例数、通过率、耗时；输出简历 3–4 条 bullet；30s/1min/3min 项目介绍；八个高频面试问答打磨。
- **禁止**：任何未经实际运行的数字。

---

## 4. 统一模块流程（引用 AGENTS.md §3）

```
需求分析 → 设计 → 实现 → 实际运行 → 测试 → MODULE_FEEDBACK
→ 独立 REVIEW → REVIEW_FEEDBACK → 修复 → 重新验证 → APPROVED → 下一模块
```

状态机：`IN_PROGRESS → WAITING_FOR_REVIEW → (NEEDS_FIX → 修复 → 复验) → APPROVED`

## 5. 风险登记册

| 风险 | 影响 | 对策 |
|------|------|------|
| Demo 数据被重置/篡改 | 用例随机失败 | 数据工厂 + 唯一命名 + 清理（M5） |
| 内部接口无文档、可能变动 | API 用例失效 | 封装层隔离，变动只改 api/ 层（M4） |
| 网络波动 | UI 用例 flaky | 先记录再治理；禁止无脑重试掩盖问题（M7） |
| 本地部署版本与 Demo 行为差异 | 结论不可互相套用 | 所有结论标注环境来源（M6） |

## 6. 当前状态

- **M0：IN_PROGRESS** —— 设计输出已完成，等待用户提交三项作业。
- M1–M11：未开始。
