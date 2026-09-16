"""DB 校验层负对照（独立复审二轮 P3-2 固化；取代"用后即删"的一次性探针）。

目的：证明 DB 校验用例真的会红——"用例永远通过"是测试的隐形失效。
机制：故意构造一个必然失败的断言（期望 lastName 与实际落库值必然不等），
并用 xfail(strict=True) 让"预期失败"不污染绿套件：
- 每次本地运行它都按设计 FAIL（显示为 xfailed）→ 证明断言真实生效
- 若断言层失效（查询错表/字段错/断言被误删），它反而会"通过"→
  strict xfail 触发 **unexpected pass** → 套件变红 → 第一时间报警
- 禁止为了恢复全绿而简单删除本用例（那是掩盖断言失效，AGENTS §14）

注意：依赖 db_client 环境门控——公网环境自动 skip（与 db 层一致）。
"""
import pytest

from api.pim import PIMApi
from config import settings
from utils.db_client import DBClient
from utils.factory import make_employee

pytestmark = pytest.mark.db

_ROW_BY_EMP_NUMBER = (
    "SELECT emp_number, emp_firstname, emp_lastname, purged_at "
    "FROM hs_hr_employee WHERE emp_number = %s"
)


@pytest.fixture
def pim_api(api_client) -> PIMApi:
    """复用 session 级 api_client（与 e2e/db 同模式）。"""
    return PIMApi(api_client)


@pytest.mark.xfail(
    strict=True,
    reason="负对照：故意写错期望 lastName，断言必须 FAIL（红）。"
           "若此用例意外 xpass = DB 校验断言已失效，套件应报警。",
)
def test_db_negative_control_always_fails(db_client, pim_api):
    """故意失败的 DB 断言：证明校验层真实生效（非永远通过）。"""
    emp = make_employee()
    resp = pim_api.create_employee(emp["firstName"], emp["lastName"], emp["middleName"])
    assert resp.ok, f"API 创建失败：{resp.status_code}"
    emp_number = resp.json()["data"]["empNumber"]
    try:
        row = db_client.query_one(_ROW_BY_EMP_NUMBER, (emp_number,))
        assert row is not None, "API 返回成功但库中无行"
        # 负对照点：唯一名是 M{ts}，与故意写错的期望必然不等
        assert row["emp_lastname"] == "DELIBERATELY_WRONG", (
            f"[负对照预期失败] 实际落库 lastName={row['emp_lastname']!r}"
        )
    finally:
        resp = pim_api.delete_employee(emp_number)
        assert resp.ok, f"清理失败（emp_number={emp_number} 残留）: {resp.status_code}"