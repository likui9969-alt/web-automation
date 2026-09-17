# 上仓前 Checklist（2026-09-17 收口核验）

> 本清单由 Builder 按全局收口审查（REVIEW_FEEDBACK.md §4 P0 三条 + §5 仍缺项）逐项核验整理。
> 每条结论均为**本机实测**结果；未验证项明确标注 UNVERIFIED，禁止在检查项上打勾代替实测。

## 一、P0 阻塞项核验（全局收口审查三条）

| # | 项 | 核验方式 | 结论（实测） |
|---|----|----------|--------------|
| P0-1 | 仓库无远程 | `git remote -v` 执行 | **仍为空（未解决）**——需要 GitHub 建远程仓库并 push，属用户操作，Builder 无法代办 |
| P0-2 | CI 从未真实运行 | 本地 act 网络不可达（历史验证） | **UNVERIFIED**——容器路径 workflow 已就绪但真实 Actions 未触发；**红线：跑绿前不投简历、不宣称"CI 已跑通"** |
| P0-3 | README 状态节停在 M6 | 读取 README.md 状态节 | **已解决**——逐模块更新至 M11，含「状态说明」诚实声明（M9 真实触发/ M10 独立复审为开放项） |

## 二、本轮收口已完成（2026-09-17，提交待定）

| 项 | 内容 | 验证 |
|----|------|------|
| 依赖精确锁定 | requirements.txt 从 `>=` 改为 `==`（pytest 9.1.1 / playwright 1.62.0 / requests 2.34.2 / pymysql 1.2.0 / allure-pytest 2.16.0） | 版本取自 venv `pip freeze` 实测；`pip check` 无冲突。锁定值 = 2026-09-16 全量 18P+1xf 实测环境 |
| 速差口径残留登记 | MODULE_FEEDBACK.md 追加 2026-09-17 记录行：M6 历史行的「~11 倍」为已被双重否决的历史结论，统一口径为「4~9 倍视用例集与时段」 | 全仓库 grep「11 倍」仅剩：历史行（已登记）、docs 纠错演练行（正确意图）、REVIEW_FEEDBACK（审查方记录，不动） |

## 三、敏感信息核验（上仓安全）

| 项 | 核查结果 |
|----|----------|
| homework/ 移出索引 | ✅ `git ls-files` 无 homework 条目（实例已 `git rm --cached`，磁盘保留） |
| .env 屏蔽 | ✅ `.gitignore` 含 `.env`；`git ls-files` 无 `.env` 条目 |
| 默认口令 | `docker/cli_install_config.yaml` 含明文口令（root_password_local 等）——**判定：本地学习环境专用默认值，非生产敏感**；与 `.env.example`、compose 默认值三处一致（README 已声明"非生产敏感"）。CI 容器路径依赖该 yaml（`docker cp`），**保留现状**。若用户顾虑，可改为 GitHub Secrets + 模板生成，但会增加首个 CI 跑绿的不确定性，不建议上仓前变更 |
| 产物目录 | ✅ reports 除 .gitkeep 外不入库（gitignore 已验证） |
| REVIEW_FEEDBACK.md 未提交改动 | `git status` 显示 M REVIEW_FEEDBACK.md——属**审查方独立维护**（AGENTS §13.1），Builder 不代写不代提交，上仓前由审查方确认 |

## 四、公开推送操作清单（用户执行）

1. GitHub 新建空白仓库（建议私有起步，面试前可转公开）
2. `git remote add origin <url>`
3. 确认工作区仅含预期变更后 `git push -u origin main`
4. 首次 push 触发真实 Actions → 观察 `docker compose up -d --wait` / 安装 / 分层跑是否全绿
5. **跑绿后**才可更新简历「CI 已跑通」表述（当前保持"workflow 已就绪"）

## 五、上仓后的开放项（不阻塞上仓，但记录）

- **M10 独立复审**：全局收口审查时 Docker daemon 不在线未复验容器内结论（E1–E6 证据已备），需审查方在 Docker 在线时独立复跑
- **M11 复审**：提交 edd7716 的整改待独立方确认（审查方当前 REVIEW_FEEDBACK.md 工作区有未提交流）
- **CI 真实跑绿闭合**：见上述 P0-2

## 六、红线（Reviewer 反复强调，上仓后仍然有效）

- ✅ 可以写：分层测试 18P+1xf / 失败留痕四件套 / API 快约 3 倍 / 本地快 4~9 倍（有实测出处）
- ❌ 不可以写：CI 已跑通（真实 Actions 未触发）、用例规模 60+（未落地）、覆盖率（未统计）、任何无法追溯到本仓库测试记录的数字