# 测试设计文档（M11 交付物，去敏版）

> 背景：`homework/` 目录因含未脱敏的作业内容已在 .gitignore 屏蔽（M11 收口审查），
> 本文件是仓库内可见的**用例设计依据**（去敏），供面试官与后续维护者直接阅读。

## 一、被测系统与硬约束（C1–C4，M0 实测）

| 约束 | 内容 | 对测试设计的影响 |
|---|---|---|
| C1 | Demo 数据库不可直连（托管服务无 MySQL 端口） | DB 校验放本地 Docker 部署（M6） |
| C2 | Demo 数据多人共享 + 定期重置 | 所有用例自造数据 + 唯一命名 + 清理（M5） |
| C3 | 无文档化公开 REST API（前端走内部接口） | 抓包 → requests 重放 = "基于抓包的内部接口测试"（M4） |
| C4 | Demo 部分操作受限 | 每个测试点以实际验证为准，未验证标 UNVERIFIED |

## 二、测试分层与配比（测试金字塔落地）

| 层 | 载体 | 用例数 | 职责 | 为什么不更多 |
|---|---|---|---|---|
| API | `tests/api` | 9 | 业务规则主力：登录鉴权边界、PIM 列表/分页/负向（422/404） | 快而稳，覆盖规则主体 |
| UI | `tests/ui` | 5 | 登录关键用户旅程（正向/错误凭证×3/空表单） | 慢且受渲染/网络影响，只测关键路径 |
| e2e | `tests/e2e` | 2 | UI+API 混合闭环：API 造数→UI 验证 / UI 添加→API 落库断言 | 金字塔顶层，双向闭环各一 |
| DB | `tests/db` | 2+1 | 持久化校验：API 操作→直查 MySQL 比对；负对照 canary（xfail strict） | 仅本地 Docker 环境 |

**速差实证**（为什么分层配比合理）：API 层 vs UI 同规模快约 3 倍；本地 vs 公网约
4~9 倍（视时段与用例集，同环境对比口径）。

## 三、关键测试设计决策（可追问：为什么这么设计）

1. **数据工厂唯一命名**（`utils/factory.py`）—— C2 的解法：前缀 + 时间戳 + 随机，
   全项目唯一；自建自清（finally 幂等删除），残留核验 = 0。
2. **fixture 三层 scope**（playwright session → browser session → page function）——
   浏览器共享省钱（+67% 用例总耗时持平），页面隔离保命（cookie/登录态不互泄）。
3. **API 造数 + UI 验证的 e2e 闭环**（conftest `ui_auth_state`）—— API 登录 cookie
   注入 Playwright storage_state 免 UI 登录（快、不依赖 SPA 渲染）。
4. **DB 层最小权限**（ohrm_ro 仅 SELECT，MySQL 侧 GRANT 强制）—— 校验层只需要读。
5. **环境门控**（conftest `db_client` 双重门控）—— 非本地环境显式 skip 而非假红；
   坏凭证下也 skip（履约顺序修复后 2 skipped 而非 2 errors）。
6. **失败留痕**（M7 收口 makereport）—— 任意层失败都落 api_log；浏览器用例另加
   截图/Trace/netlog；skip/xfail 不误记；成功零产物。

## 四、测试点清单（按功能模块）

### 登录（M0 实测 15 项 → 自动化落地哪些）

| 测试点 | 层级 | 保留原因 |
|---|---|---|
| 正确凭证登录成功（跳 /dashboard） | API + UI | 关键路径 |
| 错误密码 / 不存在用户 / 组合错误 → 统一 "Invalid credentials" | API + UI 参数化 | 防枚举实测：不区分大小写、不 trim |
| 空表单 → 必填提示 | UI | 前端校验 |
| 匿名会话访问业务接口 → 401 "Session expired" | API | 会话校验 |
| 用户名大小写 / 空格的服务端规则 | API | M0 指派 API 层（LOGIN-07/08） |
| （不测）改公共账号密码 | — | 职业道德决策，M0 记录 |

### PIM（M4–M6 实践覆盖，M0-lite 收口决策）

- 员工列表结构 + 关键字段（API-04）
- limit 分页语义：返回条数受控、total ≥ 返回条数（API-05，语义断言防竞态）
- 无效查询参数 422 / 删除不存在记录 404（API-08/09 负向）
- 创建员工 → DB 落库核验（persisted）
- 删除员工 → DB 行物理消失（hard delete 实证）+ API 搜索归零

### e2e 混合闭环

- E2E-01：API 造数 → UI 搜索可见
- E2E-02：UI 添加 → API 落库断言 → 清理（finally 失败安全）

## 五、未验证项登记（诚实边界）

- 密码重置邮件送达、连续失败锁定机制、超长输入边界、侧边栏点击不导航原因
  —— M0 已记录入作业文件，不得当作已验证事实引用
- CI 真实 GitHub Actions 触发（UNVERIFIED，上仓后闭环）