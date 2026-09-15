# Review Feedback

> 用途：独立审查某一模块的实现、测试设计和学习结果。
> 审查者：Review Agent
> 原则：独立判断，不接受主 Agent 的自我评价作为事实依据。

---

## 1. 审查信息

- 项目：OrangeHRM 企业级 Web 自动化测试平台
- 模块：M1 环境搭建 + 裸登录脚本
- 阶段：M1
- 审查时间：2026-09-15
- 审查状态：完成

---

## 2. 审查范围

本次实际检查：

- [x] 代码（test_login_bare.py、config/settings.py、pytest.ini、conftest.py、requirements.txt）
- [x] 测试（独立复跑，见 §8）
- [x] 测试设计（对照 homework/M0_登录模块作业.md 的实测测试点）
- [x] 配置（pytest.ini markers、settings.py 环境变量覆盖）
- [x] 文档（README.md、MODULE_FEEDBACK.md M1 各记录）
- [ ] Git 提交（**无法审查：本机 git 未安装，仓库未初始化**——本身即审查发现，见 P1-1）
- [x] 模块反馈（MODULE_FEEDBACK.md 验证记录逐条与实际环境核对）
- [x] 实际运行结果（Reviewer 亲自复跑，非采信 Builder 自述）

---

## 3. 总体评价

### 总评分

85 / 100

### 结论

❌ NEEDS_FIX（存在 1 个 P1：版本控制缺失。M1 核心目标本身全部达成且复验通过，但 P1 未解决前禁止进入 M2）

---

## 4. 正确项

### 4.1 测试设计

- 3 个用例覆盖正向（LOGIN-01）/ 异常（LOGIN-02 错误密码）/ 边界（LOGIN-03 空表单），测试点全部来自 M0 实测作业，无凭空设计的用例
- 断言内容基于实际观察到的行为："Invalid credentials" 原文、2 处 Required、URL 不跳转——不是"想当然应该这样"
- `expect(required).to_have_count(2)` 用数量断言验证两处字段各自校验，比只验证一处更完整

### 4.2 工程实现

- 等待策略全部基于 `expect` 自动轮询，**零固定 sleep**——与 M0 发现的"SPA 提交后 1~3 秒重渲染瞬态"风险直接对应，说明前序实测结论落到了代码里
- 配置与代码分离：`config/settings.py` 全部支持环境变量覆盖，`BASE_URL` 可切换到本地 Docker 环境（M6 依赖此前瞻设计）
- `pytest.ini` 的 `--strict-markers` 是正确的防御性配置：拼错 marker 直接报错而非静默跳过
- `pytestmark = pytest.mark.ui` 模块级打标，新增用例不会忘记 marker
- conftest.py 占位文件写明了"为什么现在是空的"——先痛后治的对照策略在文档层面闭环

### 4.3 测试稳定性

- Reviewer 独立复跑：**3 passed in 29.78s，退出码 0**（Builder 记录 35.29s）。两次运行均通过，时间差异 ~18% 恰好体现了"每用例自建浏览器 + 公网 Demo 站"的固有波动，为 M2 fixture 优化提供了可信的对照基线
- 用例之间零数据依赖、零执行顺序依赖（登录测试不产生持久数据）

### 4.4 学习理解

- 代码注释解释的是"为什么"（为什么用 placeholder 定位、为什么等 URL 而不是 sleep），不是复述操作步骤
- MODULE_FEEDBACK 的自评诚实区分了"故意保留的痛点"和"缺陷"，未粉饰

---

## 5. 问题

### P1 - 重要问题

- **P1-1：版本控制缺失（git 未安装、仓库未初始化）**
- 证据：`where.exe git` 找不到可执行文件；项目根目录无 `.git/`；README/PLAN 技术栈均含 Git，M9 CI 完全依赖 git
- 影响：① M2 将重构 M1 代码，无版本控制 = 无回滚能力，重构失败只能手工恢复；② AGENTS.md 的 Review 门禁依赖"变更可追溯"（Reviewer 应能 diff 本次改动），当前无法实现；③ M1 名为"环境搭建"，版本控制属于环境基础设施，缺失名不副实
- 修复建议：安装 Git for Windows → `git init` → 首次提交（.gitignore 已就位，`.venv/`、`.playwright-browsers/` 均已排除）。**安装软件需项目所有者操作或授权**

---

### P2 - 一般问题

- **P2-1：README"快速开始"在本机不可复现**
  - 证据：README 写 `playwright install chromium`，但实际安装走了 `PLAYWRIGHT_DOWNLOAD_HOST`（npmmirror 镜像）+ `PLAYWRIGHT_BROWSERS_PATH`（项目内路径）；且**运行**测试同样需要设置 `PLAYWRIGHT_BROWSERS_PATH`（Reviewer 复跑时必须手动设置，未设置则找不到浏览器二进制）
  - 影响：新机器（或 CI、或换目录执行）按 README 操作会失败：国内网络下官方 CDN 挂起 + 找不到浏览器
  - 修复建议：README 快速开始补两行环境变量说明，或提供 `setup.ps1`/运行脚本统一封装
- **P2-2：README"项目状态"节与实际进度不一致**
  - 证据：仍写 "[ ] M1：Playwright 裸登录脚本（待浏览器二进制安装）"，实际已 3 passed
  - 影响：违反项目"只记录实测事实"原则的反面——记录了过时的非事实
  - 修复建议：更新为实测结果

---

### P3 - 优化建议

- `browser.close()` 在断言之后手动调用：断言失败时该行不执行，浏览器进程依赖 `with sync_playwright()` 退出兜底清理。裸脚本时代的真实痛点，M2 fixture 的 `yield + teardown` 结构会自然解决——**记录为重构对照点即可，M1 不必修**
- `headless=True` 硬编码：调试失败用例时无法快速切有头模式，M2 配置化
- `"wrongpass123"` 硬编码在用例内：测试数据分离是 M2+ 主题，届时随参数化一并处理

---

## 6. 测试设计审查

### 测试覆盖（登录模块 15 个测试点中 M1 只取 3 个——合理性判断）

- 正常场景：✅ LOGIN-01
- 异常场景：✅ LOGIN-02（错误密码）；❌ 未覆盖：错误用户名、大小写混合（M0 实测发现用户名不区分大小写——这是一个有业务价值的用例，建议 M2 参数化时补）
- 边界场景：✅ LOGIN-03（空表单）；未覆盖：超长输入（M0 已登记为未验证项）
- 权限场景：N/A（Demo 只有 Admin 公开账号，PIM/Leave 模块再涉及）
- 状态流转：部分覆盖（登录成功/失败停留）；登出后回退 M0 已手工实测，自动化留待 session fixture 后成本低时补

### 分层是否合理

UI：✅ 合理。登录是关键用户旅程，且 M0 实测确认无公开 API 文档、登录 POST 细节未捕获，UI 层是当前唯一可行层。3 个用例的量级符合"少而精"
API：暂无（M4 起，符合计划）
其他：无过度 UI 自动化迹象

### 是否存在过度 UI 自动化

- 无。3 用例全部属于"必须走浏览器"的场景

### 是否存在重复测试

- 无重复用例。但**样板代码重复 ×3**（建浏览器/关浏览器）——这是 M1 有意为之的教学设计，已在自评中如实登记，不算违规

---

## 7. 工程化审查

- [x] Fixture 是否合理：M1 按"先痛后治"策略故意不抽 fixture，conftest 占位说明清晰，可接受
- [x] POM 是否合理：同上，M3 主题，当前定位器仅 3 处重复，尚未到必须抽象的阈值
- [x] 测试数据是否隔离：账号为 Demo 公开账号（只读使用），无数据创建，无污染
- [x] 命名是否清晰：`test_login_场景_预期结果` 一眼可读
- [ ] 代码是否重复：样板 ×3（有意保留，见 §6）
- [x] 异常处理是否合理：M1 无需 try/except（失败即测试失败，正确做法）
- [ ] 日志是否足够：无日志（M7 失败定位模块统一解决，当前用例少可接受）
- [x] 配置是否与代码分离：settings.py + 环境变量覆盖 ✅
- [x] 环境是否可切换：BASE_URL 可切本地 Docker（M6 用）
- [ ] **版本控制：缺失（P1-1）**

---

## 8. 稳定性审查

- 固定测试数据：仅依赖 Demo 公开账号 `Admin/admin123`——**共享环境风险**：若他人改密（M0 已做不测该项的职业道德决策），所有用例连锁失败。缓解：settings.py 支持环境变量覆盖密码；M6 本地环境后此风险归零
- 时间依赖：无
- 网络依赖：强依赖公网 Demo 站（当前阶段不可避免，M6 本地化解决）。两次运行时间差 35.29s vs 29.78s 佐证网络波动存在，但 expect 轮询 + 10s 默认超时足以吸收
- 元素定位：placeholder 定位在 M0 已确认是当前 DOM 下的唯一选择（无 label 绑定），暂无更稳方案
- 等待机制：✅ 无 sleep，全 expect 轮询
- 测试执行顺序依赖：无
- 数据污染：无（只读操作）
- Demo 数据被重置后的影响：无（不依赖任何业务数据）

---

## 9. 面试能力审查

基于代码注释、自评文档和 M0→M1 的决策链路判断：

- 为什么这样设计：✅ 能讲（先痛后治、对照基线策略在文档中完整呈现）
- 为什么选择 UI/API：✅ 能讲（登录无可用 API，M0 抓包已实证）
- 为什么使用这个技术：✅ 基本能讲（expect 轮询 vs sleep 的取舍有实证；Playwright vs Selenium 的选型理由未见于文档，**建议面试前补**）
- 遇到问题怎么解决：✅ 能讲（CDN 被墙 → 镜像方案是真实排查过程，含"5 分钟 0% 判断不可达"的决策依据）
- 如果扩大规模怎么办：⚠️ 部分（自评提到了 M2/M3 方向，但无量化对比——M2 完成后用 35.29s vs 重构后耗时的实测数据补强最有说服力）

评分：

- 理解程度：8/10
- 工程思维：8/10
- 测试思维：8/10
- 表达能力：7/10（Playwright 选型理由、量化对比待补）

---

## 10. 必须修改的问题

1. **P1-1**：安装 git + `git init` + 首次提交（含 M1 全部成果）。进入 M2 的硬性前置条件
2. **P2-2**：README"项目状态"节更新为 M1 实测事实

（P2-1 建议随 P2-2 一并处理，但允许延到 M2 开工前）

---

## 11. 建议修改的问题

1. P2-1：README 快速开始补 `PLAYWRIGHT_BROWSERS_PATH`/镜像说明（或封装脚本）
2. P3：headless 配置化、错误密码数据外置（随 M2 参数化处理）

---

## 12. 审查结论

### 当前状态

NEEDS_FIX → **APPROVED**（后记：P1-1/P2-2/P2-1 已于同日全部闭环，git 仓库 c93f61e + 6d00a65，详见 MODULE_FEEDBACK 验证记录）

### 下一阶段前置条件

必须完成：

- P1-1：git 安装 + 仓库初始化 + 首次提交
- P2-2：README 状态节更正
- M1 自评中的面试准备补强项（Playwright 选型理由）不阻塞，但 M2 Review 会复查

---

## 13. Reviewer Notes

值得长期沉淀的经验：

1. **Reviewer 复跑是必要的**：Builder 报 35.29s、Reviewer 跑出 29.78s——时间数据不采信单次运行，波动本身（~18%）就是"每用例自建浏览器"成本的证据
2. **"环境搭建"类模块的 Review 要包含工具链完整性**：不只看测试代码，git/依赖管理/可复现性都是环境的一部分（本次 P1 即来自这里）
3. **国内网络是长期约束**：Playwright CDN 镜像方案要沉淀进 README，CI（M9）里同样要配镜像，否则 GitHub Actions 国内 runner 会踩同一个坑
4. **文档漂移要即时修**：README 状态节过期看似小事，但项目明文承诺"只记录实测事实"，过时的"待安装"同样是失真

---
---

# M2 审查：Fixture + 参数化（2026-09-15）

## 审查信息

- 模块：M2 Fixture + 参数化重构
- 审查范围：conftest.py、tests/ui/test_login.py、config/settings.py、MODULE_FEEDBACK M2 记录、git 提交 428b987、独立复跑
- 审查方式：Reviewer 亲自复跑 + 逐文件走查 + 对照骨架承诺（data/.gitkeep、README 目录说明）

## 独立复跑

**5 passed in 45.82s，退出码 0**。第三次运行（Builder 36.32s / 本次 45.82s，波动 +26%）——公网 Demo 站时间数据必须看多次运行区间，不能看单点（M1 Review 已有同款结论，进一步坐实）。

## 正确项

1. **三层 fixture scope 决策正确**：browser session 共享省启停开销，page/context function 级隔离防用例间状态污染——性能与隔离的边界划在 context 上，不是拍脑袋
2. **yield 前后置语义正确**：断言失败也保证 `context.close()`/`browser.close()` 执行，M1"断言挂了 close 走不到"的痛点就此消解
3. **参数化有实测依据**：3 组错误凭证复用 M0"防枚举→统一 Invalid credentials"结论，错误用户名场景首次进入回归，不是凑数参数
4. **性能对照诚实**：MODULE_FEEDBACK 明确记录"总时长没降反微升（用例多了 2 个），省的是 ~2s/例启停，大头是公网加载"——没有夸大 fixture 收益
5. HEADLESS 配置化兑现 M1 Review 的 P3

## 问题

### P2 - 一般问题

- **P2-1：data/ 目录承诺未兑现（文档与实现不一致）**
  - 证据：`data/.gitkeep` 明写"M2 放登录负向参数组"，但参数组实际硬编码在 `test_login.py` 的 `parametrize` 装饰器内
  - 影响：项目明文的"测试数据与代码分离"原则在 M2 未落地；后续模块若沿用此模式，data/ 将永久空置成摆设
  - 修复建议：参数组外置到 data/ 模块（Python 模块即可，5 组数据不值得引入 YAML/JSON 解析依赖——KISS）

### P3 - 优化建议

1. `HEADLESS` 解析仅认 `"true"`：`ORANGEHRM_HEADLESS=1/yes` 会被当 false。文档注明只接受 true/false 即可，不必改代码
2. 提交 428b987 显示 create+delete 而非 rename（重写幅度超 git 相似度阈值），`log --follow` 无法自动追溯——旧版仍可经 c93f61e 提取，非实质问题，记录即可
3. 未来引入 pytest-xdist 并行时，session 级 browser 会每 worker 一份（预期行为，届时再评估，当前无 xdist 不算问题）

## 审查结论

### 当前状态

**APPROVED_WITH_FIXES**（P2-1 顺手修复后即可转 APPROVED；P2 允许进入下一阶段但必须修复）

### 面试能力评估

- fixture scope 取舍：✅ conftest 注释 + 自评均有依据
- yield teardown：✅
- 参数化设计：✅ 有 M0 实测支撑
- 性能归因：✅ 诚实（加分项）
- 待观察：M3 POM 重构时对"何时抽象"的判断（不要为了 POM 而 POM）

---
---

# M3 审查：POM（2026-09-15）

## 审查信息

- 模块：M3 Page Object Model
- 审查范围：pages/login_page.py、conftest.py、tests/ui/test_login.py、config/settings.py、MODULE_FEEDBACK M3 记录、独立复跑
- 审查方式：独立复跑 + 逐文件走查 + 变更传播半径核算

## 独立复跑（本次审查的高光：复跑暴露了 Builder 未见的真问题）

Reviewer 首跑（wait_until 修复后、超时仍 10s 时）：**3 passed + 2 errors**——与 Builder 同代码的 5 passed 并存，坐实"时段性环境过载"。修复 2（超时 20s 校准）后终态 **5 passed in 43.24s**。
若 Reviewer 采信 Builder 的"5 passed"自述，此环境阈值问题将潜伏到 CI 阶段才爆发。

## 正确项

1. **变更传播半径 7→0 达成**：M2 版 7 处定位器调用（placeholder×4 + role×3）散在 3 用例；M3 版测试层零定位器，全部集中于 LoginPage.__init__ 三行。前端改版成本从"逐用例排查"变为"改一处"
2. **URL 知识归 PO**：测试不再拼接 auth/login 路径；BASE_URL 切换（M6 本地 Docker）时测试零改动
3. **断言分层取舍有明确注释**：expect_logged_in（URL 是页面知识）入 PO，业务断言（错误提示可见）留测试——比"全放 PO"或"全放测试"都更有辩护力
4. **wait_until="domcontentloaded" 是正确修复**：SPA 等待条件选型，非掩盖问题的加大超时；修复后且更快（35.43s vs 此前 45-64s）
5. **超时 10→20s 校准留痕**：注释写明实测依据（过载时 DOM ready >10s），符合"环境参数按数据校准"而非"为通过放宽标准"（§14 合规）
6. flaky 排障过程全程留痕（首跑 2P+3E → 二跑 1F+4P → 双修复 → 终态 5P），证据链完整

## 问题

### P2 - 一般问题

无

### P3 - 优化建议

1. `expect_logged_in` 的 dashboard URL 正则硬编码在 PO——页面知识归属正确，但 M5 登录态复用（PIM 用例需先登录）时可能要抽 DashboardPage 与之呼应，届时重构
2. `submit_empty` 与 `login` 有轻微语义重叠（后者不可用于空值场景），当前两个方法各自语义清晰，不必强行合并
3. `url` property 直通 `self.page.url`——可接受的便利暴露，不建议继续加这类透传（PO 不是 page 的全量代理）

## 审查结论

### 当前状态

**APPROVED**

### 面试能力评估

- POM 价值能用数字讲（7→0）：✅
- 断言放哪能讲出取舍：✅
- flaky 排障有完整真实案例：✅（本模块最大收获，可直接用于"讲一次你排查不稳定测试的经历"）
- 何时不用 POM：⚠️ 建议口头补练"如果只有 1 个用例值不值得建 PO"的判断

---
---

# M4 审查：API 层（2026-09-15）

## 审查信息

- 模块：M4 API 层（Requests）
- 审查范围：api/client.py、api/pim.py、tests/api/test_pim_employees.py、conftest.py、requirements.txt、MODULE_FEEDBACK M4 记录（六轮探测）、独立复跑

## 独立复跑

`pytest -m api`：**5 passed in 15.87s**（与 Builder 14.34s 同区间）。全量 `pytest`（零环境变量）：**10 passed**，conftest setdefault 修复在不同终端条件下成立。

## 正确项

1. **六轮探测是"实际系统行为优先"原则的教科书示范**：四次合理推测（表单/CSRF/JSON/UA）全部证伪，最终靠 Playwright 网络监听一锤定音（`_token` 字段名 + `/web/index.php` 路径前缀）。全程证伪链留痕，无一步虚构
2. **client.login() 返回 bool 而非抛异常**：登录失败是可测场景（API-02 断言 False），异常只留给"页面结构变更"这类环境性故障——错误处理分层正确
3. **PIMApi 语义封装兑现骨架承诺**（.gitkeep："用例写 pim.list_employees() 而不是裸 requests.post()"）
4. **API-03 断言用实测文案 "Session expired"**，非想当然的 "unauthorized"
5. **分页测试的 total 一致性断言**（limit=1 时 total==全量 total）是业务语义级验证，超出简单状态码检查
6. **金字塔实测证据**：API 5 条 14.34s vs UI 5 条 43.24s（3 倍），README/简历可引用的数字
7. **conftest setdefault 彻底闭环 M1 P2-1**：全量运行暴露"忘设环境变量 UI 全挂"后，从文档级修复升级为代码级修复，setdefault 保留外部覆盖能力（CI 兼容）

## 问题

### P2 - 一般问题

- **P2-1：PIMApi 忽略 client.base_url（封装一致性漏洞）**
  - 证据：`PIMApi.__init__` 接受 `client` 参数，但 `list_employees` 的 URL 直取 `settings.BASE_URL`
  - 影响：传入自定义 base_url 的 client（本地 Docker 环境测试的既定设计，M6 依赖）时，PIMApi 仍打公网地址——潜伏的功能性 bug
  - 修复：URL 改用 `self.client.base_url`

### P3 - 优化建议

1. `pim` fixture 为 function 级：API-04/05 各自完整登录一次。会话复用是 M5 主题（storage_state），届时统一处理，当前 14s 无优化必要
2. `_TOKEN_RE` 耦合 HTML 结构——已用 RuntimeError 快速失败兜底（页面改版第一时间暴露），可接受
3. API-05 调两次 list（limit=1 与全量）断言 total 一致——网络抖动间隙 total 变化（共享环境他人加人）会造成偶发失败；概率极低（毫秒级窗口），M6 本地环境后自然消失，记录在案

## 审查结论

### 当前状态

**APPROVED_WITH_FIXES → APPROVED**（后记：Builder 已完成 P2-1 修复——api/pim.py URL 改用 `self.client.base_url`，复跑 `pytest -m api` 5 passed in 16.57s 退出码 0，验证记录见 MODULE_FEEDBACK 2026-09-15 P2-1 修复行。M4 关闭）

### 面试能力评估

- 接口测试怎么设计：✅ 正向/负向(401)/结构/分页四象限
- 会话维持（Cookie）怎么讲：✅ 有完整探测实证
- 抓包定位：✅ Playwright 网络监听是超出常规预期的亮点
- 金字塔为什么 API 做主力：✅ 有本项目实测数字（3 倍速差）

---
---

# M5 审查：UI+API 混合造数（2026-09-15）

## 审查信息

- 模块：M5 UI+API 混合造数（数据工厂 / 会话复用 / e2e 闭环）
- 审查范围：utils/factory.py、api/pim.py（create/delete/search 扩展）、conftest.py（api_client/ui_auth_state/ui_auth_page）、pages/pim_page.py、tests/e2e/test_pim_hybrid.py、pytest.ini（e2e marker）、MODULE_FEEDBACK M5 记录（探测→排障→实测全链路）、独立复跑

## 独立复跑

全量 `pytest`（零环境变量，与 Builder 同日不同时段）：**12 passed in 104.26s**（Builder 111.68s，均全绿，~7% 波动属公网 Demo 站正常区间）。M5 修复的断言超时校准（expect_logged_in 20s）在 Reviewer 侧同样生效。

## 正确项

1. **混合闭环分层教科书级**：造数/清理/存在性断言全走 API，UI 只承担关键用户路径（搜索验证 / 表单提交）。e2e 仅 2 条，量级符合金字塔顶层"少而精"——没有为了"混合"而混合
2. **唯一命名有双重实证支撑**：M0（3 分钟 315→316）+ M5 探测时段（331→363），factory 设计（时间戳+随机，肉眼可读）直接对应 C2 约束，不是教条式 best practice
3. **会话复用方案有工程深度**：API 登录 cookie → storage_state 注入，规避 UI 登录的 SPA 渲染波动（M3 flaky 教训的体系化应用）；conftest 注释明确 page（匿名，登录测试专用）与 ui_auth_page（带登录态）的边界——防止"用已登录状态测登录"的经典错误
4. **Save 后竞态的排障是 M5 最大亮点**：网络监听定位根因（前端先发 employeeId 唯一性校验再 POST，点击后 ~2s 落库）→ toast 业务语义等待修复，注释留痕。这是"正确等待条件 > 加大超时"原则的第二次应用（第一次 M3 domcontentloaded）
5. **expect 5s 盲区的发现**：M3 超时校准只覆盖操作层，断言层盲区由 M5 全量暴露并修复——修复跨层系统性问题的意识
6. **探测方法论进化可量化**：M4 登录探测六轮证伪 → M5 创建 API 一次命中（风格认知积累：`/api/v2/*` 是 JSON API），但删除 API 仍走了变体证伪——不因上轮成功就跳过实证
7. **empNumber/employeeId 两套编号的教训**（探测中 exists 误报）写进 api/pim.py 文档字符串——错误转化为文档

## 问题

### P2 - 一般问题

- **P2-1：E2E-02 清理不在失败安全路径上**
  - 证据：`test_ui_created_employee_exists_via_api` 中 `assert matched` 失败时，其后的 `pim_api.delete_employee(...)` 不执行
  - 影响：用例失败 = UI 已创建的员工残留共享环境。AGENTS §6（测试结束清理）只在用例**通过**时成立
  - 修复：清理移入 finally（或 fixture teardown）：失败时重新搜索唯一名 → 删除

### P3 - 优化建议（不阻塞）

1. E2E-01 fixture teardown 的 delete 无结果校验（静默失败）——当前单员工场景幂等性够用，M6 本地环境后可加孤儿数据清理策略
2. ui_auth_state 硬编码 `httpOnly: True`——当前系统仅一个 orangehrm cookie（M0 实测），多 cookie 场景需从 Set-Cookie 响应头解析属性
3. 其余 expect 断言（error_message/required_hints/to_be_visible 等）仍是 5s 默认超时，仅 expect_logged_in 校准了 20s——统一断言预算策略建议 M7 失败定位体系时一并处理
4. unique_tag 同秒并发碰撞概率 = 千分之一 × 同时段同进程，实际可忽略，不阻塞

## 审查结论

### 当前状态

**APPROVED_WITH_FIXES → APPROVED**（后记：Builder 已完成 P2-1 修复——E2E-02 清理移入 finally，失败路径重新搜索唯一名再删。复跑 `pytest -m e2e` 2 passed in 31.83s 退出码 0；**清理真实性核验：API 搜索今日 "M5091" 前缀残留 = 0**。验证记录见 MODULE_FEEDBACK 2026-09-15 P2-1 修复行。M5 关闭）

### 面试能力评估

- 测试数据管理怎么讲：✅ 唯一命名 + 自造自清 + 双重实证，完整
- 测试独立性怎么讲：✅ 能区分"用例间依赖"与"用例与环境依赖"，fixture scope 取舍有明确理由（function 隔离 vs session 速度）
- flaky test 主要来源怎么讲：✅ 本模块新增两个实证——竞态类（Save 后立即断言）与环境类（expect 5s 盲区 × 公网过载）
- UI 断言 vs API 断言的差异：✅ E2E-01/02 双向设计正是这个问题的活答案
- 会话复用/storage_state：✅ API cookie 注入方案 + 使用边界注释，超出"会用"层面的理解
