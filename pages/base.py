"""pages/base.py — 页面对象共享导航辅助（独立复审二轮 P2-1/P3-4 抽取）。

背景：LoginPage / PimPage 的 open() 曾各自复制一份 goto 单次重试逻辑（DRY
违背），且重试是否触发完全不可观测——"Demo ui 3/3"无法区分"flaky 消失"
与"flaky 被重试救回"。本文件把重试收敛到一处，并用模块级计数器 + conftest
的 pytest_terminal_summary 在会话结束输出，使重试可观测（P2-1 闭环）。
"""
from playwright.sync_api import Page, TimeoutError

from config import settings

# 模块级重试计数：key = 页面 URL，value = 本次会话 goto 重试触发次数
# 会话结束由 conftest.pytest_terminal_summary 输出（计数 > 0 即显式可见）
RETRY_COUNT: dict[str, int] = {}


def goto_with_retry(page: Page, url: str) -> None:
    """goto + 单次重试（AGENTS §14：重试仅用于吸收环境噪声，已记录在案）。

    窄捕获 Playwright 的 TimeoutError（MRO 为 TimeoutError→Error→Exception，
    与 Python 内建同名类不同族——2026-09-16 二轮复审插桩实测确认不会误捕获），
    连接拒绝等非超时异常直接上抛，不由重试掩盖。
    上限 2 次：单次 open 最坏等待 = 2 × settings.DEFAULT_TIMEOUT
    （隐含预算说明见 config/settings.py 注释）。
    """
    for attempt in (1, 2):
        try:
            page.goto(url, wait_until="domcontentloaded")
            return
        except TimeoutError:
            if attempt == 2:
                raise
            RETRY_COUNT[url] = RETRY_COUNT.get(url, 0) + 1