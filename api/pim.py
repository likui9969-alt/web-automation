"""api/pim.py — PIM 模块接口语义封装。

用例写 pim.list_employees(limit=1)，不写裸 URL：
内部接口路径/参数名变了只改这里，测试层零改动（对齐 pages/ 的思路）。

响应结构（2026-09-15 实测）：
    {"data": [{empNumber, lastName, firstName, middleName, employeeId, ...}],
     "meta": {"total": 331}, "rels": [...]}

M5 补充实测（2026-09-15 探测）：
- POST JSON body 即可创建员工（无需额外 header）
- DELETE 走 JSON body {"ids": [empNumber]}（路径参数 405，查询参数 422）
- 按名搜索用 ?name=（模糊匹配 first/last；lastName 是无效参数 → 422）
- empNumber（主键 int）与 employeeId（显示编号 str，如 "0544"）是两套编号
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

    def search_by_name(self, name: str, limit: int = 50, offset: int = 0):
        """GET 按名搜索（模糊匹配 first/last，M5 实测）。"""
        return self.client.session.get(
            f"{self.client.base_url}/web/index.php/api/v2/pim/employees",
            params={"name": name, "limit": limit, "offset": offset},
            timeout=settings.DEFAULT_TIMEOUT,
        )

    def create_employee(self, first_name: str, last_name: str, middle_name: str = ""):
        """POST 创建员工（M5 实测：JSON body → 200，data.empNumber 为主键）。"""
        return self.client.session.post(
            f"{self.client.base_url}/web/index.php/api/v2/pim/employees",
            json={"firstName": first_name, "middleName": middle_name,
                  "lastName": last_name},
            timeout=settings.DEFAULT_TIMEOUT,
        )

    def delete_employee(self, emp_number: int):
        """DELETE 删除员工（M5 实测：JSON body {"ids": [n]}，主键 empNumber）。"""
        return self.client.session.delete(
            f"{self.client.base_url}/web/index.php/api/v2/pim/employees",
            json={"ids": [emp_number]},
            timeout=settings.DEFAULT_TIMEOUT,
        )
