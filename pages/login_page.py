"""LoginPage — 登录页 Page Object（M3 激活 pages/ 层）。

POM 解决的问题（用 M2 版数字说话）：
M2 里 7 处定位器调用散在 3 个用例中（placeholder×4 + role×3）。
前端把 placeholder "Username" 改名 → 测试要改 2 处；
按钮从 <button> 换成 <div role=...> → 要改 3 处。
M3 后：3 个定位器定义集中在本文件，**前端改版只改这里，变更传播半径 7→0**。

设计取舍（面试常问"断言放 PO 还是测试"）：
- PO 收编：定位器、URL、操作序列（登录页知道怎么登录）
- 测试保留：业务断言（"错误凭证应提示 Invalid credentials"是测试关注点，
  不是页面知识）。例外 expect_logged_in：URL 模式属于页面细节，测试不必知道
"""
import re

from playwright.sync_api import Page, expect

from config import settings


class LoginPage:
    URL_PATH = "/web/index.php/auth/login"

    def __init__(self, page: Page):
        self.page = page
        # M0 实测：输入框无 label 绑定，placeholder 是唯一语义定位
        self.username_input = page.get_by_placeholder("Username")
        self.password_input = page.get_by_placeholder("Password")
        self.login_button = page.get_by_role("button", name="Login")

    def open(self) -> "LoginPage":
        # wait_until="domcontentloaded"：SPA 只需 DOM 就绪即可交互，
        # 不必等全部图片/字体的 load 事件——公网高峰期 load 等待随机超时的
        # 正确解法（改等待条件，不是无脑加大超时）
        self.page.goto(f"{settings.BASE_URL}{self.URL_PATH}", wait_until="domcontentloaded")
        return self

    def login(self, username: str, password: str) -> None:
        """用户视角的完整登录操作。"""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def submit_empty(self) -> None:
        """不填任何值直接提交（LOGIN-03 前端校验场景）。"""
        self.login_button.click()

    # ---- 供测试断言用的页面状态 ----

    @property
    def error_message(self):
        """M0 实测：错误提示统一文案（防用户枚举）。"""
        return self.page.get_by_text("Invalid credentials")

    @property
    def required_hints(self):
        return self.page.get_by_text("Required")

    @property
    def url(self) -> str:
        return self.page.url

    def expect_logged_in(self) -> None:
        """登录成功的页面状态（URL 细节属于页面知识，测试不必关心）。"""
        expect(self.page).to_have_url(re.compile(r"/dashboard/index"))
