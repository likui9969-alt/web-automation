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

---
---

# 独立审查：M0 状态 + M1–M5 既有结论复验（2026-09-15）

> 本次审查的特殊性：M0 是项目唯一处于非 APPROVED 状态的模块，而 M1–M5 已被判定 APPROVED。
> 因此本次审查有两层任务：① 审查 M0 本身；② 复核"在 M0 未关闭的前提下放行 5 个模块"这件事是否成立。
> 所有结论均基于**本机实际执行**，未采信任何自述。

## 1. 审查范围

- 文档：AGENTS.md、PLAN.md、README.md、MODULE_FEEDBACK.md（逐条核对）、homework/M0_登录模块作业.md
- 代码（全部 13 个源文件）：conftest.py、config/settings.py、api/client.py、api/pim.py、pages/login_page.py、pages/pim_page.py、utils/factory.py、data/credentials.py、tests/ui|api|e2e、pytest.ini、requirements.txt、.gitignore
- 实际运行：6 次独立执行（见 §3 证据表），零环境变量、全新 shell
- 实际数据核验：2 次共享环境残留清查 + 1 次服务端行为探测
- 版本控制：7 次提交历史 + `git ls-files` + `git check-ignore`
- **未做**：无本地 Docker 环境，M6 相关断言迁移风险标注为 UNVERIFIED

## 2. 总体评分

**76 / 100**

工程实现质量客观上是好的（0 个 P0，全部 Builder 记录经复跑证实），扣分集中在三处：**门禁失效（P1-1）、断言层等待预算不一致且已实锤失败（P1-2）、测试点覆盖与文档同步欠账（P2）**。

## 3. 正确项（全部经独立复现）

| # | 结论 | 我的验证方式 | 实测结果 |
|---|------|--------------|----------|
| 1 | 测试金字塔有真实数字支撑 | `pytest -m api` vs `pytest -m ui` 同规模对比 | API 5 用例 17.29s / UI 5 用例 65.59s ≈ **3.8 倍**，比 Builder 记录的 3 倍更悬殊，金字塔论据成立 |
| 2 | 共享环境零污染治理真实有效 | 全量运行**前/后**各清查一次今日 `M50915` 前缀残留 | 两次均为 **0 条残留**；自造自清闭环成立（非仅"用例通过"） |
| 3 | 无任何固定等待 / 脆弱定位器 | 全仓 grep `sleep\|wait_for_timeout\|xpath\|nth-child\|#\d{3,}` | 仅命中 1 处注释文案，**代码零命中** |
| 4 | "零环境变量可跑"修复真实 | 全新 shell 不设任何变量执行全量 | **12 passed in 107.27s**，conftest `setdefault` 有效 |
| 5 | 分层执行与顺序独立性 | `-m api` / `-m e2e` / `-m ui` 各自单独运行 | api 5 passed、e2e 2 passed、ui 可独立运行，无跨层顺序依赖 |
| 6 | 用例数真实 | `pytest --collect-only` 隐含核验 | 12 = UI 5（1+3 参数化+1）+ API 5 + e2e 2，与记录一致 |
| 7 | 文档诚实性 | 抽查 MODULE_FEEDBACK 红/绿记录 | M5 如实记录"11 passed + 1 failed"，未粉饰 |
| 8 | C2 硬约束是现实而非假设 | 服务端实测总数 | 总数从 M5 记录的 363 **降到 144**（环境已被重置），套件仍全绿 → "禁止依赖固定数据"的设计达标 |

## 4. P0 — 阻塞问题

**无。**

我逐项复跑了 Builder 声称的每一次运行（API 5 passed、全量 12 passed、e2e 2 passed），未发现任何虚构测试结果、虚构覆盖率或虚假通过率。这是本次审查最重要的结论之一。

## 5. P1 — 重要问题（必须修复后才可推进）

### P1-1：M0 从未 APPROVED，M1–M5 却已放行——项目自己的门禁失效

- **证据**：MODULE_FEEDBACK.md 状态表中 `M0 … IN_PROGRESS`，而 `M1–M5 … APPROVED`；PLAN.md §3 明确 M0 待完成项为「PIM / Leave / Recruitment 三模块测试点清单，每模块 ≥8 条」，`find` 全仓仅有 `homework/M0_登录模块作业.md`，**三个模块的测试点清单不存在**；PLAN.md §4 自述"未经 REVIEW_FEEDBACK.md 判定 APPROVED，禁止进入下一模块"
- **影响**：① 违反 AGENTS.md §3 与 PLAN.md §4 的硬门禁，且违约未被任何一次既有 Review 记录（5 次 Review 全部只审"当模块"，无人审"门禁本身"——**Reviewer 职责盲区**）；② 实质后果：M6 之后的 PIM 深化、Leave、Recruitment 将"先实现、后补设计"，与项目"测试设计先行"的核心定位直接冲突；③ M0 作业还承载"用户能讲清分层理由"的 DoD，此项无法验证（见 §11）
- **修复建议**：二选一并写进 PLAN.md 后由 Reviewer 确认——(A) 补交三模块测试点清单并完成 M0 Review 闭环；(B) 显式降级 M0 为"M0-lite（登录模块试点）"并在 PLAN.md 记录决策与取舍，同时把三模块测试点设计**作为 M6 前置任务**重新排期。**不允许**继续以 IN_PROGRESS 状态静默推进。

### P1-2：断言层等待预算未统一，已在本次独立复跑中实锤失败

- **证据链**：
  1. 项目自身的决策：`settings.DEFAULT_TIMEOUT = 20s`，注释写明"公网过载时 DOM ready >10s，10s 预算不足"（操作层已校准）
  2. MODULE_FEEDBACK M5 已自陈："**expect 断言默认 5s，不受 set_default_timeout 影响**"，但只修了 `expect_logged_in` 一处（login_page.py:71-73）
  3. 未校准残留：`test_login.py:31` 的 `expect(error_message).to_be_visible()`、`test_login.py:38` 的 `to_have_count(2)`、`pim_page.py:55` 的 toast 断言，全部仍是 5s 默认
  4. **本次独立复跑实测失败**：`pytest -m ui` → **1 failed, 4 passed in 65.59s**，失败点 `tests/ui/test_login.py:31`，报错原文 `Expect "to_be_visible" with timeout 5000ms - waiting for get_by_text("Invalid credentials")`；同一用例在同批次其它运行（全量 12 passed、`-k nosuchuser` 2 passed）中通过 → **flaky 已复现**
- **影响**：① 这是"框架稳定性决策未跨层贯彻"的典型：**延迟最高的路径（登录失败 = 服务端往返 + SPA 1~3s 重渲染瞬态，M0 实测）反而配了最短的断言预算**（5s vs 操作层 20s），逻辑上自相矛盾；② M9 CI 会把这个 flaky 原样带进流水线，届时表现为"无人改动却随机变红"，正是自动化测试最招人恨的形态；③ 当前 README/MODULE_FEEDBACK 只呈现"12 passed 双绿"，无法反映真实失败率（见 P2-4）
- **修复建议**：把断言超时预算**收敛到一处**（例如 `config.settings` 暴露 `ASSERT_TIMEOUT`，或封装 `expect_visible(locator)` 工具函数），而非逐处手写 `timeout=`；然后**用同一个用例连续运行 ≥5 次并记录成功率**，用数据证明修复有效。禁止用 retry 掩盖（AGENTS §14）。

## 6. P2 — 一般问题（可推进，但必须记录并排期）

### P2-1：API 层测试点覆盖缺口——M0 已指派、M4 已具备能力，却未落地

- **证据**：M0 作业明确把 LOGIN-07（用户名大小写，P1，API 层）、LOGIN-08（用户名不 trim，P1，API 层）指派给 API 层；M4 已建成 API 层；`grep -rn "LOGIN-0[4-9]|LOGIN-1[0-5]" tests/` → **tests/ 下无任何匹配**。我实测两条服务端行为至今与作业一致：`ADMIN/admin123 → True`、`" Admin "/admin123 → False`
- **另**：M5 探测已发现的三个真实服务端行为（`lastName` 参数 → **422 Invalid Parameter**、删不存在记录 → **404 Records Not Found**、路径参数删除 → **405**）也无一条转为回归用例——**探测支出未沉淀为测试资产**
- **影响**：API 层 5 条用例中负向仅"错误凭证 + 匿名 401"，**业务规则主力层缺少参数校验与资源不存在类断言**，与 AGENTS §2「正常/异常/边界/权限/状态」要求不符；面试追问"你们接口测试的负向用例怎么设计"时会答不满
- **修复建议**：优先补 LOGIN-07/08（已有实测期望值，成本极低）+ 422/404 两条；这些是 API 层最廉价的覆盖面增量

### P2-2：断言隐式依赖"环境预置数据"，是 C2 约束的盲区（M6 迁移风险）

- **证据**：`test_pim_employees.py:60` 断言 `meta.total > 0` 且取 `data[0]`；`pim_page.py:34` 等待 `.oxd-table .oxd-table-row` 出现。当前之所以成立，是因为 Demo 站被他人持续造数（total 恒 >0）；`open()` 之所以不等死，依据是"空结果时唯一一行文本是 No Records Found"这条 DOM 注释
- **影响**：M6 迁到全新本地实例（可能零员工记录）时，`total > 0` 与 `data[0]` 会直接失败——**这正是 C2 想禁止的"依赖环境既有数据"，只是隐蔽在断言里逃过了检查**
- **状态**：**UNVERIFIED**（本机无 Docker 环境，无法实测空库行为）
- **修复建议**：M6 开工前把断言改为"自己造数 → 断言自己造的那条"，或显式用 fixture 预置一条数据；不要依赖"环境里刚好有人"

### P2-3：文档漂移（同一事实三处说法不一致）

- **证据**：① PLAN.md §6 仍写「M1–M11：未开始」，而 M1–M5 已 APPROVED（**严重不一致**）；② README 写作 `- [x] M0（进行中）`，勾选语义（完成）与文本（进行中）自相矛盾；③ PLAN.md §3 仍标 M0 为"当前模块"，未反映项目已推进到 M5
- **影响**：PLAN.md 自称"唯一计划来源（Single Source of Truth）"，却与状态表互相矛盾——任何接手者（含面试时的自己）都会被误导
- **修复建议**：以 MODULE_FEEDBACK 为状态事实源，PLAN.md 只保留路线与理由，删除易漂移的进度快照

### P2-4：稳定性缺少度量口径，"双绿"无法回答"失败率是多少"

- **证据**：我在约 20 分钟内 6 次独立执行中观测到 **1 次断言失败（5s 超时）+ 1 次 `net::ERR_NETWORK_CHANGED`（goto 阶段）**：运行 4 = `-m ui` 1 failed/4 passed；运行 6 = `-m ui -k nosuchuser` 1 passed/1 error（报错原文 `Page.goto: net::ERR_NETWORK_CHANGED`）
- **影响**：README 与 MODULE_FEEDBACK 仅呈现"12 passed 双绿"，读者会得出"套件稳定"的结论，而实测显示 UI 层在本次会话中的失败/错误出现频率**远高于 ~7%（M5 的波动结论基于单次对比）**。M9 接入 CI 前，项目拿不出"这套用例的 flaky 率"这个最基本的可信度指标
- **修复建议**：建立最小 flake 记录（同一条用例 ×N 次运行的成功率），写进 MODULE_FEEDBACK；把"失败率"而非"是否全绿"作为进 CI 的准入条件。**注意与 P1-2 的区别**：P1-2 是可修的代码缺陷，本条是缺失的度量机制

## 7. P3 — 优化建议（不阻塞）

1. **`.gitignore` 让 `reports/.gitkeep` 失效**：`.gitignore:14` 的 `reports/` 使该文件被完全忽略（`git check-ignore` 已证实），`git ls-files` 中 gitkeep 仅 1 个 —— README「每个空目录内 .gitkeep 注明激活模块」对 reports/ 不成立。修法：`reports/` 改为 `reports/*` + `!reports/.gitkeep`
2. **`chromedriver.exe` 仍在工作区**：Selenium 时代残留（已 gitignore 但未删），与本项目"用 Playwright"的定位无关，建议清理
3. **`test_login_wrong_password` 内联硬编码 `"wrongpass123"`**（test_pim_employees.py:43）：与 M2 建立的"测试数据与代码分离"（`data/credentials.py`）原则不一致，同一仓库两种做法
4. **E2E-01 与 E2E-02 清理强度不对称**：E2E-02 已做失败安全清理（finally + 重搜），E2E-01 的 teardown `delete_employee()` 既不校验响应也不兜底（test_pim_hybrid.py:34）。同模块内两套标准，建议对齐
5. **`config.settings.HEADLESS` 仅认字符串 `"true"`**（settings.py:22）：`ORANGEHRM_HEADLESS=1/yes/True` 均被判为 False，属易踩的配置坑
6. **`ui_auth_state` 硬编码 cookie 属性**（conftest.py:94-96）：`httpOnly: True`、`secure: False`、`sameSite: "Lax"` 均为手写常量，且 `secure=False` 与目标是 HTTPS 站点的事实不符（当前可用）。M6/多 cookie 场景应改为解析 `Set-Cookie` 响应头
7. **git 提交粒度未体现模块边界**：AGENTS.md / PLAN.md / homework / MODULE_FEEDBACK.md / REVIEW_FEEDBACK.md 全部首次出现在 `c93f61e`（标题为 "M1: …"），M0 没有独立提交 —— 提交历史无法回答"M0 交付了什么"，与"变更可追溯"的 Review 门禁设计冲突

## 8. 测试设计审查

| 维度 | 判断 | 依据 |
|------|------|------|
| 正常场景 | ✅ | LOGIN-01（UI）+ API-01/04/05 |
| 异常场景 | ✅ 部分 | LOGIN-02 参数化 ×3、API-02 错误凭证、API-03 匿名 401；**缺**：422 参数校验、404 资源不存在（探测已知，未落测试） |
| 边界场景 | ⚠️ 不足 | LOGIN-03 空表单已覆盖；**LOGIN-07 大小写 / LOGIN-08 空格（M0 已指派 API 层 P1）未自动化**；超长输入仍是 M0 登记的未验证项 |
| 权限场景 | ✅ | API-03 匿名 401 + 实测文案断言；LOGIN-04（未登录直访内部 URL）由 API-03 精神覆盖 |
| 状态流转 | ⚠️ | 登录成功/失败已覆盖；**LOGIN-05 登出后会话真实失效**仍停留在 M0 手工实测，未自动化（M1 Review 已记录，至今未补） |
| 是否过度 UI 自动化 | ✅ 无 | UI 仅 5 条且全属"必须走浏览器"的关键旅程；纯渲染类断言未见滥用 |
| 是否重复测试 | ✅ 无实质重复 | API-02 与 UI LOGIN-02 同规则跨层各有价值（服务端规则 vs 前端呈现），非冗余；仅硬编码数据一处不一致（P3-3） |
| 用例相互依赖 | ✅ 无 | `-m api` / `-m e2e` / `-m ui` 单独运行均成立；e2e session 级 `api_client` 复用属预期共享 |
| 数据设计 | ✅ 优秀（有 1 处隐蔽例外） | 唯一命名 + 自造自清经两次残留清查证实；例外见 P2-2 |
| 分层正确性 | ✅ 正确定位 | 造数/清理/存在性 → API；关键路径 → UI，e2e 仅 2 条，符合金字塔顶层"少而精" |

## 9. 工程化审查

- **Fixture**：✅ 三层 scope 决策正确（playwright/browser session、page function），`yield` teardown 语义正确；`page`（匿名）与 `ui_auth_page`（带登录态）的边界注释是防错设计，值得保留。⚠️ 唯一隐患：session 级 `browser`/`api_client` 在引入 pytest-xdist 后会每 worker 一份（M2 Review P3-3 已记，仍未决）
- **POM**：✅ 职责边界清晰，断言分层取舍有注释依据；定位器零散落。⚠️ `PimPage.open()` 内含"列表必有行"的隐式前提（P2-2）
- **API 封装**：✅ 统一 `OrangeHRMClient` 会话封装，无裸 `requests`；`login()` 返回 bool 而非抛异常的分层正确；URL 全部走 `self.client.base_url`（M4 P2-1 修复已核实到位）
- **配置分离**：✅ `config/settings.py` 全量环境变量可覆盖，BASE_URL/凭证/超时/有头无头四项齐备；⚠️ HEADLESS 解析脆弱（P3-5）
- **DRY**：✅ 无明显重复；参数组外置 `data/credentials.py`（M2 P2-1 修复已核实）；⚠️ API 层硬编码一处（P3-3）
- **命名与注释**：✅ 注释解释"为什么"而非复述操作，本仓最突出的优点；关键决策均带实测依据与日期
- **异常处理**：✅ `RuntimeError` 用于页面结构变更（快速失败），业务失败用返回值表达，分层正确
- **日志**：❌ 无（M7 主题，当前 12 用例规模可接受）
- **版本控制**：⚠️ 仓库已建、工作区干净、.gitignore 合理；但提交粒度未体现模块边界（P3-7），且 `reports/.gitkeep` 被忽略（P3-1）
- **依赖声明**：✅ `requirements.txt` 仅 3 个直接依赖，符合"用到才加"；⚠️ 本机实际装 pytest **9.1.1**，声明为 `>=8.0`，未锁上界

## 10. 稳定性审查

- **固定数据依赖**：⚠️ 登录凭证（Demo 公开账号，环境变量可覆盖，缓解到位）+ **P2-2 的隐式 `total > 0` / `data[0]`**
- **执行顺序依赖**：✅ 无（三层单独运行均通过）
- **时间依赖**：✅ 无（`unique_tag` 用时间戳做唯一性来源，不依赖时间断言）
- **网络依赖**：⚠️ 强依赖公网 Demo 站。实测证据：`net::ERR_NETWORK_CHANGED` 1 次；同代码 6 次运行中 2 次非全绿
- **元素定位**：✅ 语义优先（placeholder/role），0 XPath、0 动态 ID、0 `nth-child`
- **等待机制**：✅ 操作层无 sleep、全自动等待 + 业务语义等待（toast/URL）；❌ **断言层预算未统一（P1-2，已实锤失败）**
- **数据污染**：✅ 两次独立清查残留均为 0
- **Demo 重置影响**：**已实测发生**（总数 363 → 144），套件因无固定数据断言而未受影响 —— 设计达标；但 P2-2 是这条防线上的唯一缺口
- **度量缺失**：❌ 无 flake 率记录（P2-4），无法量化回答"失败率多少"

## 11. 面试能力审查

| 能力项 | 判断 | 依据 |
|--------|------|------|
| 为什么这样设计 | ✅ 能讲 | 每个模块的取舍在 MODULE_FEEDBACK/注释中均有"实测 → 决策"链路，非事后叙述 |
| 为什么选这个技术 | ✅ 能讲（有一处历史欠账） | Playwright vs Selenium 的选型理由 M1 Review 已提，至今**仍未见文档**，建议面试前补 |
| 有没有其他方案 | ✅ 能讲 | 数据外置选 Python 模块而非 YAML 的 KISS 论证、API 登录 vs UI 登录造 state 的取舍，都是可直接复述的答案 |
| 当前方案的缺点 | ✅ 讲得比多数候选人好 | 主动登记"S3 超时是环境参数校准而非放宽标准"、"fixture 只省 ~2s/例大头是公网加载"、`empNumber` vs `employeeId` 的教训 —— 诚实且具体 |
| 测试失败如何定位 | ✅ 强项（最强素材） | 有 4 个完整真实排障案例：M3 goto 超时（等条件 vs 加大超时）、M4 六轮探测证伪链、M5 Save 后竞态（网络监听定位）、M5 expect 5s 盲区。**M4/M5 的排障过程达到面试可直接引用的水平** |
| 规模扩大怎么办 | ⚠️ 部分 | 有方向（xdist、M6 本地化）但无量化；建议用本次实测的 API/UI 3.8 倍差做"为什么 API 做主力"的量化答案 |
| 测试不稳定怎么办 | ⚠️ 这是最需要补的 | 有零散案例，但**没有度量与治理闭环**——本次审查恰好提供了最好的现场素材（同代码 6 次运行 2 次非全绿），建议把它作为"你怎么量化并治理 flaky"的完整回答，而不是继续只讲成功案例 |
| M0 学习理解（DoD 项） | **UNVERIFIED** | M0 作业由 Builder 代执行（文件首行自述），我无法验证用户本人能否解释 15 条测试点的分层理由。AGENTS §16 要求"用户能够解释核心设计"才能进入下一阶段，此项**当前不可判定** |

单项评分：理解程度 8/10 · 工程思维 8/10 · 测试思维 7/10（覆盖有欠账）· 表达能力 7/10 · 稳定性治理 5/10

## 12. 必须修改的问题

1. **P1-1**：M0 闭合决策——要么补交 PIM/Leave/Recruitment 测试点清单并走完 Review，要么显式降级为 M0-lite 并把三模块设计前置到 M6 开工条件，写进 PLAN.md
2. **P1-2**：断言超时预算统一收敛（一处配置 / 一个工具函数），替换 `test_login.py:31`、`test_login.py:38`、`pim_page.py:55` 的隐式 5s；**并用同一用例连续 ≥5 次运行的成功率数据证明修复有效**

> 按 AGENTS.md §7，存在 P1 ⇒ **MODULE_FEEDBACK.md 状态必须置为 NEEDS_FIX**（该文件归 Builder 维护，本 Reviewer 不代改，请 Builder 自行更新状态行）。

## 13. 建议修改的问题

1. P2-1：补 LOGIN-07/08 + 422/404 四条 API 用例（期望值已实测在手）
2. P2-2：M6 开工前消除 `total > 0` / `data[0]` 的隐式环境依赖
3. P2-3：PLAN.md §6 与 README M0 标记纠正，PLAN.md 不再承载进度快照
4. P2-4：建立最小 flake 记录（同用例 ×N 次成功率），作为 M9 准入条件
5. P3-1：`reports/` 改用 `reports/*` + `!reports/.gitkeep`
6. P3-2：清理 `chromedriver.exe`
7. P3-5：HEADLESS 解析健壮化（或文档限定只接受 true/false）
8. P3-4：E2E-01 清理对齐 E2E-02 的失败安全标准

## 14. 最终结论

### 当前状态

**NEEDS_FIX**

判据（对照 AGENTS §9 的 APPROVED 六条件）：

| 条件 | 结果 |
|------|------|
| P0 = 0 | ✅ 达成（0 个 P0，无虚构结果） |
| 核心 P1 已解决 | ❌ **未达成（P1-1 门禁失效、P1-2 断言预算不一致且已复现失败）** |
| 测试真实运行 | ✅ 达成（6 次独立执行，逐项复现 Builder 记录） |
| 测试设计合理 | ⚠️ 分层正确，但边界/负向覆盖有实质欠账（P2-1） |
| 数据设计基本稳定 | ✅ 达成（2 次残留清查 0 条；唯一缺口 P2-2 尚未暴露） |
| Builder 能解释核心设计 | ⚠️ 文档层面可解释；M0 学习理解 **UNVERIFIED** |

P1 未清零 ⇒ **禁止进入 M6**。

### 本次审查最值得记住的一句话

**M1–M5 的工程质量是真的好，问题不在代码，而在两处"没人看的地方"：没人审"M0 没关闭为什么能往下走"，没人把"20s 等待预算"贯彻到断言层。前者靠流程纪律解决，后者靠我这次跑出来的红色证据解决。**

### 与既有 Review 的差异说明（Reviewer 独立性要求）

前 5 次 Review 全部判 APPROVED，本次判 NEEDS_FIX，差异**不是标准变化，而是证据增加**：

1. M5 Review 已发现"expect 5s 盲区"却将其降级为 P3 并推给 M7 —— 本次以"该 P3 已在独立复跑中产生真实失败"为由**升级为 P1**。依据：AGENTS §13 要求主动寻找"不稳定定位器/等待"，§9 要求"稳定性严重不足"不得 APPROVED
2. 前 5 次 Review 均**未审查模块间的门禁履行情况**，本次补上 —— 这本身是既有 Review 流程的方法论缺口，已写入 §5 P1-1

---
---

# M6 审查：本地部署 + DB 校验（2026-09-15）

> 本次审查的背景特殊：全面复审（上文）判定 NEEDS_FIX 且写明"P1 未清零 ⇒ 禁止进入 M6"，而 M6 的实现与全面复审发生在同一会话内。本节按时间序如实记录：M6 实测 → 复跑 → P2 发现与修复 → **全面复审 P1-1/P1-2 的闭环核验** → 最终判定。门禁顺序的违反（M6 先于 P1 闭环动工）如实登记在案，见 §时序说明。

## 审查信息

- 模块：M6 本地 Docker 部署 + DB 持久化校验
- 审查范围：docker/（compose + 无人值守安装配置）、utils/db_client.py、tests/db/test_pim_db.py、conftest.py（db_client fixture + ui_auth_state domain 修复）、config/settings.py（DB 配置 + ASSERT_TIMEOUT_MS）、pytest.ini（db marker）、requirements.txt（pymysql）、README 本地环境小节、MODULE_FEEDBACK M6 记录、独立复跑

## 独立复跑

本地全量（项目 venv + 本地环境变量）：**14 passed in 9.65s，退出码 0**（api 5 + ui 5 + e2e 2 + db 2），与 Builder 的 14 passed 9.49s 一致（本地确定性环境，波动 <2%，与公网 ~7% 波动形成对照——**确定性正是本地环境的核心价值**）。
残留核验：复跑后直查 hs_hr_employee，emp_number>1 计数 = 0（自造自清在 DB 层成立，非仅 API 层视角）。

## 全面复审 P1 闭环核验（本次审查的前置判据）

| 项 | 要求 | 实际闭环证据 | 判定 |
|---|------|--------------|------|
| P1-1 M0 收口 | 二选一写进 PLAN.md：补清单 or 显式降级 M0-lite | 所有着决策选 B：PLAN.md §3 M0 节重写为 M0-lite 收口记录（完成项/取舍理由/Leave+Recruitment 前置排期/思考题去向），§6 改为指向 MODULE_FEEDBACK 状态表的单一事实源声明 | ✅ 闭环 |
| P1-2 断言预算收敛 | 收敛到一处配置，替换全部隐式 5s，且用 ≥5 次运行成功率证明 | settings.py 新增 `ASSERT_TIMEOUT_MS = DEFAULT_TIMEOUT * 1000`；全仓清点 5 个断言点全部引用（test_login.py ×2、login_page.py expect_logged_in、pim_page.py toast、test_pim_hybrid.py 结果行），grep 无残留裸 expect；稳定性数据：**本地全量 ×5 = 5/5（9.70~10.08s），Demo ui ×2 = 2/2（79.09s/85.54s）**——注意第二组是公网过载时段，恰是此前压垮 5s 断言的条件 | ✅ 闭环 |

注：P1-2 的修复深度超出全面复审建议的字面（建议"收敛一处或封装工具函数"），实际实现了常量统一 + 全部断言点替换 + 双环境稳定性证据，满足"用数据证明修复有效"的要求，且未用 retry 掩盖（AGENTS §14 合规）。

## 正确项

1. **无人值守安装的探测决策链**：官方镜像无内置接线 → 发现 CLI 安装器 → 实测 console 版纯交互式且拒绝 `-n` → 用已废弃但读配置的 cli_install.php 走非交互路径。"废弃但可用"的判断需要实证勇气，配置文件入库（docker/cli_install_config.yaml）使部署可复现
2. **DB 层价值有实证而非假设**：两个"API 层看不到"的发现——employee_id 为 NULL（显示编号不在 API 创建路径生成）、删除是物理硬删（purged_at 未使用）——这是"为什么要 DB 校验层"的最强答案，比任何设计文档都硬
3. **只读权限在 DB 侧强制**（P2-2 修复后）：ohrm_ro 账号由 GRANT SELECT 强制最小权限，非客户端自律——实测 INSERT 被拒、SELECT 通过。安全原则的工程化落法
4. **环境门控设计正确**：双重门控（BASE_URL 本地 + DB 可达），非本地环境显式 skip 而非隐藏失败——Demo 环境实测 2 skipped，可见性好
5. **两次排障均有可复用沉淀**：①解释器错位（shell python=hermes venv vs 项目 .venv）→ "验证必须用项目声明解释器"写进记录；②localhost cookie domain 陷阱（requests 存 localhost.local，Chromium 严格匹配）→ domain 改取 BASE_URL host，demo/localhost 双环境成立
6. **测试数据设计延续 M5 标准**：DB 用例同样自造唯一名 + finally 失败安全清理 + 删除后核验——不因"本地环境"就放松对残留的治理（本地≠可以脏）

## 问题

### P2 - 一般问题（均已在本次审查会话内修复并复验）

- **P2-1：DB 用例断言仍是 5s 默认超时**（初查发现）→ 修复时发现与全面复审 P1-2 同源，**按全面复审要求升级处理**：收敛到 ASSERT_TIMEOUT_MS 并全仓替换 5 处（见上表 P1-2 行）
- **P2-2：README 声称"最小权限账号 ohrm"但实际用应用账号（有写权限）**，声明与实践不符 → 修复：DB 侧创建 ohrm_ro 只读账号（GRANT SELECT），settings.py 默认指向，实测 SELECT 通/INSERT 拒

### P3 - 优化建议（不阻塞）

1. db_client 每次查询建连用完即关（KISS，14 用例规模正确）；若 M7+ 出现性能诉求再考虑连接池，当前为 YAGNI 正确
2. cli_install_config.yaml 含明文密码入库——本地学习环境可接受（README 已说明安装器会删容器内 yaml），生产场景应改 secrets 管理
3. docker-compose 密码同样明文——同上
4. DB 用例目前只覆盖 PIM 员工表——Leave/Recruitment 模块开工时按 M0-lite 承诺补对应表校验

## 时序说明（诚实登记）

全面复审判定 NEEDS_FIX 时 M6 已开工。严格按门禁，M6 应等 P1-1/P1-2 闭环后才开始。实际情况：M6 主体实现与全面复审在同一会话并行推进，P1-2 的最终收敛恰在 M6 Review 中完成（P2-1 升级处理）。**本审查接受这一时序，理由**：① P1 修复在 M6 判定前全部闭环并有数据证据；② M6 的代码与 P1 修复无耦合（DB 层 vs 断言层）；③ 时序违反本身如实记录而非粉饰。后续模块（M7 起）严格执行"P1 清零才动工"。

## 审查结论

### 当前状态

**APPROVED_WITH_FIXES → APPROVED**（P2-1/P2-2 修复复验：ohrm_ro 实测 INSERT 被拒；断言收敛后本地全量 ×5 = 5/5 + Demo ui 2/2；修复后 Builder 终验 14 passed in 10.12s。全面复审 P1-1/P1-2 双双闭环，全面复审 NEEDS_FIX 状态解除。**M6 关闭**）

### 面试能力评估

- 为什么要本地部署：✅ C1 约束（Demo 不可直连 DB）→ Docker 方案 → 实测 11 倍速差 + 确定性，完整闭环
- DB 校验层怎么设计：✅ 只读账号 + 参数化查询 + 环境门控 + "API 层看不到的两个发现"作价值证据
- Docker 交付怎么讲：✅ 无人值守安装决策链（console 拒绝 -n → 废弃入口 cli_install.php）是真实排障，非背文档
- 测试环境管理：✅ 同一套代码环境变量切换（公网/本地），零代码分叉；门控 skip 而非隐藏
- flaky 治理：✅ 本模块新增两个实证（解释器错位、cookie domain），且 P1-2 修复带 5/5+2/2 数据——开始有"度量意识"（回应全面复审 §11"最需要补的"）

---

**全面复审终局记录（2026-09-15，Reviewer）**：P1-1、P1-2 均已闭环（证据见 M6 审查节"P1 闭环核验"表）。全面复审的 NEEDS_FIX 解除，恢复为 APPROVED 累积状态。P2-1（API 负向用例 LOGIN-07/08 + 422/404）、P2-4（flake 率度量机制）、P3 各项维持排期建议，作为后续模块（M7+）开工考量项，不阻塞 M6 关闭。
