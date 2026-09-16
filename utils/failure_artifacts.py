"""utils/failure_artifacts.py — M7 失败定位体系：失败现场留痕的统一入口。

为什么需要（PLAN M7）：自动化测试一半的价值在「失败时能否 5 分钟定位」。
本模块是 conftest / api 层共用的留痕基础设施，四类产物：

1. 截图        —— page.screenshot，失败现场的像素证据
2. Playwright Trace —— context.tracing，完整操作序列 + 网络 + DOM 快照
3. 浏览器请求/响应 —— page.on("request"/"response") 收集的 netlog
4. API 请求/响应日志 —— requests.Session hooks 全局记录（含 UI 会话复用）
   （API 层失败无浏览器可截，请求日志是唯一现场）

产物一律落 reports/（已 gitignore，不入库）；命名按 nodeid 唯一化，带时间戳，
多次运行互不覆盖，可保留多次现场对比。
"""
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

# ---- 当前执行用例 nodeid（M7 Review P2-2 关联键）----
# 为什么需要：API_LOG 是全 session 扁平列表，若只有 method/url/status，
# 失败用例的 api_log 会混入整个 session 的 API 流量且无法过滤。conftest 在
# pytest_runtest_setup 时调用 set_current_nodeid 更新本值，record_api_log
# 落盘时带上当前 nodeid + 毫秒时间戳 → 日志按用例/时间可过滤。
CURRENT_NODEID: str = "unknown"


def set_current_nodeid(nodeid: str) -> None:
    global CURRENT_NODEID
    CURRENT_NODEID = nodeid


# ---- API 层全局请求日志（requests.Session hooks["response"] 追加）----
# 为什么全局：UI/API/e2e 各层会话是不同对象（function/session scope），
# 失败发生时拿不到另一个层级的 client——全局记录 + 会话结束 dump 最简。
API_LOG: list[dict] = []


def record_api_log(method: str, url: str, status: int, ms: int) -> None:
    """API 请求日志（只陪跑不拦截：纯记录，绝不影响请求/断言行为）。"""
    API_LOG.append({
        "ts": int(datetime.now().timestamp() * 1000),  # 毫秒时间戳（P2-2 可过滤）
        "nodeid": CURRENT_NODEID,                     # 当前用例归属（P2-2）
        "method": method, "url": url, "status": status, "ms": ms,
    })


def make_artifact_paths(nodeid: str) -> dict[str, Path]:
    """按失败用例 nodeid 生成 4 类产物路径（KISS：一次失败一套命名）。

    自建目录（Review P3-3）：不依赖 pytest_configure 先跑——函数该自洽，
    单独调用（如一次性脚本）也不报错。时间戳到毫秒（P3-2）：除非同一用例
    同一毫秒失败两次，否则重跑不互相覆盖。
    """
    ts = datetime.now().strftime("%H%M%S%f")[:-3]  # HHMMSS + 毫秒
    slug = (
        nodeid.replace("::", "__").replace("/", "_")
        .replace("[", "_").replace("]", "_").replace(" ", "_")
    )
    paths = {
        "screenshot": REPORTS_DIR / "screenshots" / f"{ts}_{slug}.png",
        "trace": REPORTS_DIR / "traces" / f"{ts}_{slug}.zip",
        "netlog": REPORTS_DIR / "logs" / f"{ts}_{slug}_net.json",
        "api_log": REPORTS_DIR / "logs" / f"{ts}_{slug}_api.json",
    }
    for p in paths.values():
        p.parent.mkdir(parents=True, exist_ok=True)
    return paths