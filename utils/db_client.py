"""utils/db_client.py — M6 DB 校验层：直查 MySQL 验证「业务真的落库了」。

为什么需要它（M6 面试主题：页面显示成功 ≠ 成功）：
API 返回 200 / UI 显示 "Successfully Saved" 只证明「应用层认为成功」，
不证明数据持久化正确——缓存命中、异步写失败、字段截断、触发器改写，
这些只有查库才能暴露。DB 是最终事实源（source of truth）。

放在 utils/ 而不是 api/：
api/ 封装的是「被测系统对外暴露的接口」，DBClient 是测试基础设施
（和 factory 一样服务于「怎么测」，不属于被测系统边界）。

连接策略：每次 query 建连用完即关。校验频次低（每用例 1~2 次），
为省几毫秒维持长连接，反而引入「空闲超时断连 + 重试」的复杂度（KISS）。

权限设计：专用只读账号 ohrm_ro（DB 侧 GRANT SELECT 强制，M6 Review P2-2），
不用应用账号 ohrm / root——「只读」由数据库保证而非客户端自律，
测试框架在权限层面没有误写数据的能力（实测 INSERT 被拒）。
"""
import pymysql
import pymysql.cursors

from config import settings


class DBClient:
    """只读 DB 校验客户端。连不上时抛 OperationalError，由 fixture 决定 skip。"""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ):
        self._connect_kwargs = {
            "host": host or settings.DB_HOST,
            "port": port or settings.DB_PORT,
            "user": user or settings.DB_USER,
            "password": password or settings.DB_PASSWORD,
            "database": database or settings.DB_NAME,
            "charset": "utf8mb4",
            "connect_timeout": settings.DEFAULT_TIMEOUT,
            "cursorclass": pymysql.cursors.DictCursor,
        }

    def query(self, sql: str, params: tuple | None = None) -> list[dict]:
        """执行只读查询，返回 dict 行列表。

        必须用参数化占位符 %s 传值，不拼 SQL 字符串——
        测试数据虽然不是恶意输入，但参数化是零成本的默认习惯。
        """
        with pymysql.connect(**self._connect_kwargs) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return list(cursor.fetchall())

    def query_one(self, sql: str, params: tuple | None = None) -> dict | None:
        """查单行：期望至多一条时用（配合唯一键/唯一名的 WHERE）。"""
        rows = self.query(sql, params)
        return rows[0] if rows else None
