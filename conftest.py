"""conftest.py — pytest 全局共享 fixture（M2 激活，M1 占位期的承诺兑现）。

M1 裸版（git 历史 c93f61e 可对照）每用例自建浏览器的代价：
3 用例 35.29s，其中 ~6s 是重复的浏览器启停。本文件把启停逻辑收编到一处。

三层 fixture 设计（为什么拆三层而不是一个大 fixture）：
    playwright (session) → browser (session) → page (function)
1. playwright/session：驱动进程整个会话只起一次（最重的资源）
2. browser/session：浏览器进程共享——启动 ~2s 是纯开销，用例之间无差别
3. page/function：每个用例独立 context+page——**隔离的关键**。
   Cookie/localStorage 全挂在 context 上，用例 A 的登录失败状态
   不能泄给用例 B。浏览器共享省钱，页面隔离保命，两者不矛盾。

yield 语义：之前的代码 = setup，之后的 = teardown。
断言失败也会执行 teardown（对比 M1：断言挂了 browser.close() 永远走不到）。
"""
import json
import os
from pathlib import Path

# 必须在任何 Playwright 浏览器启动前执行（M4 全量运行实测咬人：
# 新开终端忘设 PLAYWRIGHT_BROWSERS_PATH → UI 全部 error）。
# M9 P0 修复（Review P0：CI 里 PLAYWRIGHT_BROWSERS_PATH=~/... 字面 ~ 不展开，
# Playwright 相对 CWD 解析到不存在的目录 → UI/e2e 全 error）：
#   仅当项目内 .playwright-browsers 存在时才 setdefault——本机走项目内路径
#   （M4 修复不回退）；CI runner 上该目录不存在 → 不设置 → 用 Playwright
#   默认路径（Linux 即 $HOME/.cache/ms-playwright，与 playwright install 落点
#   一致）。把"环境约定"从 workflow YAML 挪回代码，消除对 runner 隐式行为的依赖。
_local_browsers = Path(__file__).parent / ".playwright-browsers"
if _local_browsers.exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(_local_browsers))

import pytest
from playwright.sync_api import sync_playwright

from config import settings
from pages.login_page import LoginPage
from utils.failure_artifacts import make_artifact_paths


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright):
    browser = playwright.chromium.launch(headless=settings.HEADLESS)
    yield browser
    browser.close()


def pytest_configure(config):
    """M7 留痕基础设施：失败 nodeid 收集容器 + 产物目录就位。

    目录统一用 failure_artifacts.REPORTS_DIR（绝对路径）而非相对 Path("reports")
    ——相对路径取决于 CWD，IDE 运行器/CI 下 CWD ≠ 项目根时产物目录会建到别处，
    而 make_artifact_paths 用的是绝对路径，两套来源必打架（Review P2-1）。
    """
    config.m7_failed_nodeids = set()
    from utils.failure_artifacts import REPORTS_DIR

    for d in (REPORTS_DIR / sub for sub in ("screenshots", "traces", "logs")):
        d.mkdir(parents=True, exist_ok=True)


def _dump_failure_artifacts(item, call, paths):
    """统一留痕收口（M7 P1-1 修复）：任何层失败都尽量留下现场。

    为什么从「fixture teardown 触发」改成「makereport 钩子触发」：
    API/DB 层用例不用浏览器 fixture，原实现里 _dump_failure_artifacts 只被
    page/ui_auth_page 的 teardown 调用 → api/db 失败永不落盘（11/19 条用例
    失败无现场）。收口后：
      - 有 page    → 截图（call 阶段 attach 进 Allure 报告，M8 实测 teardown
                     时 Allure 上下文已关闭、attach 会被静默丢弃）
      - 有 context → Playwright Trace + 浏览器 netlog
      - 无条件     → API 请求日志（API/DB 层没有浏览器，这是唯一现场）
    所有留痕失败只置对应字段为 None 并打印原因，绝不掩盖原始失败。
    paths["skipped"] 记录「某类产物为什么没有」——定位体系里"为什么没有
    产物"本身就要回答（Review P2-3）：不是静默缺失，汇总会在终端显式列出。
    """
    config = item.config
    # P2-1：append 提前到写文件之前——有产物就一定出现在汇总里，
    # 后面写文件失败只影响对应字段（置 None），不会吞掉已成功的截图/Trace。
    config.m7_failure_paths = getattr(config, "m7_failure_paths", [])
    config.m7_failure_paths.append((item.nodeid, paths))
    paths["skipped"] = []  # (kind, reason)——汇总时显示的"缺失原因"

    # 1) 截图 + Allure attach（仅 call 阶段失败且浏览器用例有 page；
    #    M8 实测仅 call 阶段 attach 有效——setup 失败时页面常处于异常中，
    #    截图大概率超时且 Allure 上下文未验证，故 setup 阶段不截图）
    #    R-04：独立 5s 超时——站点整体不可达时，失败的用例不应为截图
    #    再白等一个完整 DEFAULT_TIMEOUT（20s），放大 CI 时间。
    page = getattr(item, "_m7_page", None)
    if call.when == "call" and page is not None:
        try:
            page.screenshot(path=str(paths["screenshot"]), full_page=True, timeout=5000)
            import allure
            from allure_commons.types import AttachmentType

            allure.attach.file(
                str(paths["screenshot"]), name="failure_screenshot",
                attachment_type=AttachmentType.PNG)
        except Exception as exc:
            paths["screenshot"] = None
            paths["skipped"].append(("screenshot", f"{type(exc).__name__}: {exc}"))
    else:
        paths["screenshot"] = None
        if page is None:
            paths["skipped"].append(("screenshot", "no page fixture (API/DB 层)"))
        elif call.when != "call":
            paths["skipped"].append(("screenshot", "setup 阶段失败，不截图 (M8 边界)"))

    # 2) Trace + netlog（仅浏览器用例有 context）
    context = getattr(item, "_m7_context", None)
    netlog = getattr(item, "_m7_netlog", None)
    if context is not None:
        try:
            context.tracing.stop(path=str(paths["trace"]))
        except Exception as exc:
            print(f"[M7] Trace 导出失败（已跳过，不掩盖原失败）: {exc}")
            paths["trace"] = None
            paths["skipped"].append(("trace", f"{type(exc).__name__}: {exc}"))
        if netlog is not None:
            try:  # P2-1：netlog 写入同样包 try/except（CWD≠根或磁盘问题时不让它放大原始失败）
                paths["netlog"].write_text(
                    json.dumps(netlog, ensure_ascii=False, indent=1), encoding="utf-8")
            except Exception as exc:
                print(f"[M7] netlog 写入失败（已跳过，不掩盖原失败）: {exc}")
                paths["netlog"] = None
                paths["skipped"].append(("netlog", f"{type(exc).__name__}: {exc}"))
        else:
            paths["netlog"] = None
            paths["skipped"].append(("netlog", "no netlog attached"))
    else:
        paths["trace"] = None
        paths["netlog"] = None
        if netlog is None and context is None:
            paths["skipped"].append(("trace/netlog", "no browser context (API/DB 层)"))

    # 3) API 请求日志：无条件落盘（API/DB 层唯一现场）
    from utils.failure_artifacts import API_LOG

    if API_LOG:
        try:
            paths["api_log"].write_text(
                json.dumps(API_LOG, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as exc:
            print(f"[M7] api_log 写入失败（已跳过，不掩盖原失败）: {exc}")
            paths["api_log"] = None
    else:
        paths["api_log"] = None


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """记录当前执行用例 nodeid（M7 Review P2-2：api_log 关联键）。

    record_api_log 落盘时按 CURRENT_NODEID 打标，失败用例的 api_log
    才能从 session 级扁平列表里过滤出自己的请求。
    """
    from utils.failure_artifacts import set_current_nodeid

    set_current_nodeid(item.nodeid)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """失败用例统一留痕入口（M7 P1-1 修复：覆盖全部 4 层，不再只看浏览器用例）。

    setup/call 任一阶段失败都收口。时序依据：makereport 在 fixture teardown
    之前执行，浏览器 context 此时仍存活，trace 可安全导出；且 exit 一次只记一条。

    skip/xfail 除外：pytest.skip / xfail 也走 excinfo 非 None 的分支，
    但它们不是"失败"——DB 门控 skip、负对照 canary（xfail strict 常驻红）
    若留痕会污染汇总（全量回归实测抓到：3 skipped 全被误记）。
    """
    if call.when in ("setup", "call") and call.excinfo is not None:
        # skip/xfail 不是失败，不留痕：
        # - skip：fixture 里 pytest.skip() 抛 Skipped（DB 门控）
        # - xfail：两种情况——显式 pytest.xfail() 抛 XFailed；或带 xfail marker
        #   的用例断言失败（如负对照 canary 常驻红）。后者 excinfo.value 是
        #   AssertionError 而非 XFailed，必须靠 marker 判断（全量实测抓到）。
        if isinstance(call.excinfo.value, (pytest.skip.Exception, pytest.xfail.Exception)):
            return
        if item.get_closest_marker("xfail"):
            return
        item.config.m7_failed_nodeids.add(item.nodeid)
        _dump_failure_artifacts(item, call, make_artifact_paths(item.nodeid))


def _new_page_with_tracing(browser, **context_kwargs):
    """开一个带 M7 留痕的浏览器 context：Trace 全程录制（内存）+ 请求/响应收集。

    返回 (context, page, netlog)。成功用例 teardown 时 trace 直接丢弃，
    失败用例导出——只在失败时产生磁盘产物，成功路径零开销（除内存 trace）。
    """
    context = browser.new_context(**context_kwargs)
    # Trace 录制开关：snapshots（DOM 快照）默认开，本机/CI 均支持；
    # 容器内（M10 实测）snapshots=True 会触发 chromium TargetClosedError
    # （DOM 快照协议与容器环境不兼容的已知问题），故容器经环境变量关闭
    # snapshots、保留 screenshots（路径追踪 + 截图仍可用）
    _snapshots = os.getenv("ORANGEHRM_TRACE_SNAPSHOTS", "true").lower() == "true"
    context.tracing.start(screenshots=True, snapshots=_snapshots)
    page = context.new_page()
    page.set_default_timeout(settings.DEFAULT_TIMEOUT * 1000)
    netlog: list[dict] = []
    # 只记不改：不拦截、不影响 Playwright 行为（日志不参与断言）
    # R-10（Review P3-1）：补 elapsed（耗时）与 content-type——只有 method/url/status
    # 时"5 分钟定位"偏薄（耗时定位慢响应、content-type 定位错误响应），Trace 里有
    # 但要解压翻找，netlog 直接给最常用字段。
    page.on("request", lambda r: netlog.append({"type": "req", "method": r.method, "url": r.url}))
    page.on("response", lambda r: netlog.append({
        "type": "resp", "status": r.status, "url": r.url,
        "elapsed_ms": r.elapsed if "elapsed" in dir(r) else None,
        "content_type": r.headers.get("content-type", ""),
    }))
    return context, page, netlog


def _teardown_context(request, context):
    """浏览器 context 收尾：成功 → 丢弃 trace，失败 → 产物已由 makereport 导出。

    留痕已统一收口到 pytest_runtest_makereport（P1-1 修复）——失败用例的
    Trace/netlog/截图在 call/setup 阶段就已落盘，teardown 只需关闭 context；
    成功用例在此丢弃内存中的 trace（不产磁盘垃圾，成功零留痕保持）。
    """
    if request.node.nodeid not in request.config.m7_failed_nodeids:
        context.tracing.stop()  # 成功：丢弃 trace（不产磁盘垃圾）
    context.close()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """会话结束输出：goto 重试计数（P2-1）+ M7 失败留痕产物汇总。

    重试计数使「3/3 通过」可验证（计数>0 = flaky 被重试救回，非消失）；
    M7 汇总列出每个失败用例的截图/Trace/日志路径，5 分钟定位从这里开始。
    """
    from pages.base import RETRY_COUNT

    if RETRY_COUNT:
        lines = " · ".join(f"{url} retried x{n}" for url, n in RETRY_COUNT.items())
        terminalreporter.write_sep(
            "=", f"goto 重试（AGENTS §14 环境噪声吸收）: {lines}", yellow=True)

    paths = getattr(config, "m7_failure_paths", [])
    if paths:
        terminalreporter.write_sep("=", f"M7 失败留痕（{len(paths)} 用例）", red=True)
        for nodeid, art in paths:
            terminalreporter.write_line(f"  {nodeid}")
            skipped = art.get("skipped", [])  # 内部标记键，不当作产物打印
            for kind, p in art.items():
                if kind == "skipped" or p is None:
                    continue
                terminalreporter.write_line(f"    {kind:10s} -> {p}")
            # R-04：显式列出"为什么某类产物缺失"——不留悬念，定位从原因开始
            for kind, reason in skipped:
                terminalreporter.write_line(f"    {kind:10s} (跳过: {reason})")


@pytest.fixture
def page(browser, request):
    """匿名浏览器页（登录测试专用）。M7 起带失败留痕：失败 → 截图/Trace/log。

    _m7_page/_m7_context/_m7_netlog 挂 item：让 pytest_runtest_makereport
    在失败时可取到 page/context/netlog 统一留痕（截图、Trace、浏览器网络日志）。
    fixture teardown 时 Allure 上下文已关闭、attach 会被静默丢弃（M8 实测），
    故截图必须在 makereport 的 call 阶段做，fixture 里只负责 closing。
    """
    context, page, netlog = _new_page_with_tracing(browser)
    request.node._m7_page = page
    request.node._m7_context = context
    request.node._m7_netlog = netlog
    yield page
    _teardown_context(request, context)


@pytest.fixture
def login_page(page) -> LoginPage:
    """打开登录页并返回 Page Object——用例从此不知 URL、不知定位器。"""
    return LoginPage(page).open()


# ---- M5：共享会话（API 造数 + UI 免登录）----

@pytest.fixture(scope="session")
def api_client():
    """session 级 API 会话：整个运行登录一次，供 e2e 造数/断言/清理复用。

    与 tests/api/ 的 function 级 pim fixture 有意共存：
    API 层验证登录边界（每用例独立会话，隔离优先），
    e2e 层追求速度（共享会话，登录 ~2s 只付一次）。
    """
    from api.client import OrangeHRMClient

    client = OrangeHRMClient()
    assert client.login(settings.USERNAME, settings.PASSWORD), "session 级 API 登录失败"
    return client


@pytest.fixture(scope="session")
def ui_auth_state(api_client):
    """API 会话 cookie → Playwright storage_state（M4 Review P3-1 的会话复用）。

    为什么 API 登录而不是 UI 登录造 state：
    快（秒级）且不依赖 SPA 渲染——M3 教训：公网过载时 UI 登录的
    goto 可能随机超时，登录态构造不该被页面渲染波动劫持。
    M5 探测实测：注入 orangehrm HttpOnly cookie 后直达 PIM 列表，不跳登录页。

    domain 为什么取 BASE_URL 的 host 而不是 cookie 自带属性（M6 实测教训）：
    requests/http.cookiejar 对 localhost 会话 cookie 存成 "localhost.local"
    （cookielib 的历史怪癖），API 客户端自身不受影响（cookiejar 发送时
    特判 localhost），但 Playwright/Chromium 严格按 domain 匹配 →
    注入的 cookie 送不出去 → 被 302 回登录页。cookie 能否送达只取决于
    domain 与访问主机是否匹配，会话凭证是 value——所以 domain 直接用
    实际访问的主机，跨环境（demo 域名 / localhost）都成立。

    其余属性为何硬编码（Review P3，M2/M6 已裁定不改代码）：
    - httpOnly=True：M0 实测当前系统仅一个 orangehrm cookie 且为 HttpOnly，
      多 cookie 场景需从 Set-Cookie 解析再改（YAGNI）
    - secure=False：必须为 False——本地环境是 http://localhost:8080，
      设 True 则本地 cookie 不发送；且 secure 对会话凭证送达无影响
    - sameSite=Lax：注入用，与真实 Set-Cookie（Lax）一致
    """
    from urllib.parse import urlparse

    host = urlparse(settings.BASE_URL).hostname
    return {
        "cookies": [
            {
                "name": ck.name,
                "value": ck.value,
                "domain": host,
                "path": ck.path or "/",
                "expires": ck.expires if ck.expires else -1,  # -1 = 会话 cookie
                "httpOnly": True,  # M0 实测：orangehrm cookie 为 HttpOnly
                "secure": False,
                "sameSite": "Lax",
            }
            for ck in api_client.session.cookies
        ],
        "origins": [],
    }


@pytest.fixture  # function：每用例独立 context，仅共享登录态 cookie
def ui_auth_page(browser, ui_auth_state, request):
    """免登录 page：独立 context + 共享登录态。

    与 page fixture 的区别：page 匿名（登录测试专用，登录本身是被测对象时
    绝不能用本 fixture——那等于把被测前提变成了注入的假状态）。
    """
    context, page, netlog = _new_page_with_tracing(browser, storage_state=ui_auth_state)
    request.node._m7_page = page
    request.node._m7_context = context
    request.node._m7_netlog = netlog
    yield page
    _teardown_context(request, context)


# ---- M6：DB 校验层（仅本地 Docker 环境）----

@pytest.fixture(scope="session")
def db_client():
    """DB 校验会话：直查本地 MySQL 验证「数据真的落库了」。

    环境能力门控（不是隐藏失败）：DB 用例在公网 Demo 环境 skip，
    报告里显式可见；本地环境全量执行。
    双重门控的理由：
    1. BASE_URL 必须是本地——防止「对 Demo 实例做 API 操作、却查本地库」
       的错配：行当然查不到，那不是 bug 是环境错乱
    2. DB 必须可达——compose 没拉起时 skip 而非 error
    """
    # M10 扩展：容器化测试环境 BASE_URL=compose 服务名 http://ohrm-app
    # （非宿主 localhost，但同样是本地 Docker 被测系统）——门控须把它也当本地，
    # 否则容器内全套跑 DB 用例会假 skip（P1-1 门控思路的容器化延伸）
    if not any(h in settings.BASE_URL for h in ("localhost", "127.0.0.1", "ohrm-app")):
        pytest.skip("DB 校验仅支持本地 Docker 环境（当前 BASE_URL 非本地）")
    import pymysql

    from utils.db_client import DBClient

    try:
        client = DBClient()
        client.query("SELECT 1")
    except pymysql.err.OperationalError as e:
        pytest.skip(f"本地 MySQL 不可达，DB 校验 skip：{e}")
    return client
