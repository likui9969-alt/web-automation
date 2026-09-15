"""api/pim.py — PIM 模块接口语义封装。

用例写 pim.list_employees(limit=1)，不写裸 URL：
内部接口路径/参数名变了只改这里，测试层零改动（对齐 pages/ 的思路）。

响应结构（2026-09-15 实测）：
    {"data": [{empNumber, lastName, firstName, middleName, employeeId, ...}],
     "meta": {"total": 331}, "rels": [...]}
"""
from api.client import OrangeHRMClient
from config import settings


class PIMApi:
    def __init__(self, client: OrangeHRMClient | None = None):
        self.client = client or OrangeHRMClient()

    def list_employees(self, limit: int = 50, offset: int = 0):
        """GET 员工列表（M0 抓包确认的接口，limit/offset 分页）。"""
        return self.client.session.get(
            f"{self.client.base_url}/web/index.php/api/v2/pim/employees",
            params={"limit": limit, "offset": offset},
            timeout=settings.DEFAULT_TIMEOUT,
        )
