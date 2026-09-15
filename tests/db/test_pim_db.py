"""M6 DB 校验用例 —— API 操作与数据库持久化的一致性验证。

本层回答的核心问题（M6 面试主题）：
API 返回 200、UI 显示 "Successfully Saved"，数据就真的持久化正确了吗？
应用层的一切"成功"都只是声明；DB 行是最终事实源。

分层定位：DB 校验不是独立于 api/ui 的平行层，而是对既有操作的
「验证增强」——当被测点是数据一致性时，直接查库比"再用 API 查一遍"
更可靠（API 可能命中缓存，DB 不会）。所以本文件的操作全部复用 api 层，
只在验证环节下沉到 DB。

断言时机：操作返回后立即查库。若业务是异步落库，这个时机必然测出
竞态（先查不到后查到）——OrangeHRM 同步写库，2026-09-15 探测实测为
操作返回即可查到，无等待窗口。

实测依据（2026-09-15 _probe_m6.py 探测，非推测）：
- API 创建 → 行存在，emp_firstname/emp_lastname 与提交一致，purged_at NULL
- API 删除 → 行物理消失（硬删，purged_at 未被使用），API 搜索同步归零
- 意外发现：API 创建的员工 employee_id 为 NULL（显示编号不在 API 创建路径
  生成）——API 层看不到的真相，恰是 DB 校验层价值的直接证据。
  用例不对此断言：机制未完全查明（UI 路径行为未对照），断言它属于过度耦合
"""
import pytest

from api.pim import PIMApi
from utils.factory import make_employee

pytestmark = pytest.mark.db

_ROW_BY_EMP_NUMBER = (
    "SELECT emp_number, emp_firstname, emp_lastname, purged_at "
    "FROM hs_hr_employee WHERE emp_number = %s"
)


@pytest.fixture
def pim_api(api_client) -> PIMApi:
    """复用 session 级 api_client（与 e2e 同模式）：造数/清理走共享会话。"""
    return PIMApi(api_client)


def test_api_created_employee_persisted_in_db(pim_api, db_client):
    """API 创建员工 → hs_hr_employee 行存在且字段一致。

    这是「页面/接口显示成功 ≠ 成功」的最直接反例构造：
    如果应用存在异步写失败/字段截断/触发器改写，本用例会当场暴露。
    """
    emp = make_employee()
    resp = pim_api.create_employee(emp["firstName"], emp["lastName"], emp["middleName"])
    assert resp.ok, f"API 创建失败：{resp.status_code}"
    emp_number = resp.json()["data"]["empNumber"]
    try:
        row = db_client.query_one(_ROW_BY_EMP_NUMBER, (emp_number,))
        assert row is not None, "API 返回成功但库中无行——持久化失败"
        assert row["emp_firstname"] == emp["firstName"], "落库 firstName 与提交值不一致"
        assert row["emp_lastname"] == emp["lastName"], "落库 lastName 与提交值不一致"
        assert row["purged_at"] is None, "新建记录不应处于软删状态"
    finally:
        # 失败安全清理（M5 Review P2-1 同款教训）：断言挂了也要删数据
        pim_api.delete_employee(emp_number)


def test_api_deleted_employee_removed_from_db(pim_api, db_client):
    """API 删除员工 → DB 行物理移除（硬删）。

    删除验证的价值：M5 只从 API 搜索归零推断"删干净了"，本用例下沉到
    行级确认——如果 OrangeHRM 实际是软删（行还在 + 标记位），API 视角
    看不出来，只有查库知道。实测为硬删，断言按真实行为写。
    """
    emp = make_employee()
    resp = pim_api.create_employee(emp["firstName"], emp["lastName"], emp["middleName"])
    assert resp.ok, f"前置创建失败：{resp.status_code}"
    emp_number = resp.json()["data"]["empNumber"]

    assert pim_api.delete_employee(emp_number).ok, "API 删除失败"

    row = db_client.query_one(
        "SELECT emp_number FROM hs_hr_employee WHERE emp_number = %s",
        (emp_number,),
    )
    assert row is None, "API 已删但行仍留在库中（实测为硬删，应物理移除）"
