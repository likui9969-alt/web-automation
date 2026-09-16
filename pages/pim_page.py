"""PimPage — PIM 页面对象（M5：e2e 混合用例所需的最小集）。

只收编 e2e 用到的能力：搜索、结果行、添加员工表单。
不追求 PIM 全功能覆盖（YAGNI——用例驱动，用到了再加）。

M5 探测实测（2026-09-15，DOM 摸底）：
- 姓名搜索框是自动补全输入（placeholder "Type for hints..."），
  页面有两个（Employee Name / Supervisor Name），first 是员工姓名
- 表格行 ".oxd-table .oxd-table-row"；空结果显示 "No Records Found"
- Add 表单：First/Middle/Last Name placeholder + Save 按钮
"""
from playwright.sync_api import Page, TimeoutError, expect

from config import settings


class PimPage:
    URL_PATH = "/web/index.php/pim/viewEmployeeList"

    def __init__(self, page: Page):
        self.page = page
        self.name_input = page.get_by_placeholder("Type for hints...").first
        self.search_button = page.get_by_role("button", name="Search")
        self.add_button = page.get_by_role("button", name="Add")
        self.first_name_input = page.get_by_placeholder("First Name")
        self.middle_name_input = page.get_by_placeholder("Middle Name")
        self.last_name_input = page.get_by_placeholder("Last Name")
        self.save_button = page.get_by_role("button", name="Save")

    def open(self) -> "PimPage":
        # SPA 同款等待策略（M3 教训）：domcontentloaded + 首行 attached
        # 首行到达 = 列表数据渲染完成，搜索框已可交互
        try:
            self.page.goto(f"{settings.BASE_URL}{self.URL_PATH}", wait_until="domcontentloaded")
        except TimeoutError:
            # goto 单次重试（独立复审 P1-2 整改）：与 LoginPage.open() 同款——
            # 公网共享 Demo 导航超时是环境噪声，AGENTS §14 合规的重试仅吸收噪声、
            # 到第二次为止，不改变断言与结论
            self.page.goto(f"{settings.BASE_URL}{self.URL_PATH}", wait_until="domcontentloaded")
        self.page.wait_for_selector(".oxd-table .oxd-table-row", state="attached")
        return self

    def search(self, name: str) -> "PimPage":
        """搜索操作本身不等结果——结果断言交给 expect 自动轮询（M1 原则）。"""
        self.name_input.fill(name)
        self.search_button.click()
        return self

    def add_employee(self, first_name: str, last_name: str, middle_name: str = "") -> None:
        """列表页 → Add → 填表 → Save（UI 关键路径）。

        Save 后必须等 "Successfully Saved" toast——M5 诊断实测：前端先发
        employeeId 唯一性校验、再 POST 创建（点击后 ~2s 才落库），不等
        系统成功反馈就断言 = 竞态扑空。等 toast 是业务语义等待，非固定 sleep。
        """
        self.add_button.click()
        self.first_name_input.fill(first_name)
        self.middle_name_input.fill(middle_name)
        self.last_name_input.fill(last_name)
        self.save_button.click()
        # 断言预算统一取 settings.ASSERT_TIMEOUT_MS（全面复审 P1-2 修复）
        expect(self.page.get_by_text("Successfully Saved")).to_be_visible(
            timeout=settings.ASSERT_TIMEOUT_MS
        )

    # ---- 供测试断言用的页面状态 ----

    @property
    def result_rows(self):
        """结果行。空结果时唯一一行的文本是 No Records Found。"""
        return self.page.locator(".oxd-table .oxd-table-row")

    @property
    def empty_result_hint(self):
        return self.page.get_by_text("No Records Found")
