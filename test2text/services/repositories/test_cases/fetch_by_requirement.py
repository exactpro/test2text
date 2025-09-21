from test2text.services.db import DbClient


def fetch_test_cases_by_requirement(
    db: DbClient, requirement_id: int, radius: float, limit: int
) -> list[tuple[int, str, str]]:
    sql = """
        SELECT DISTINCT
            TestCases.id as case_id,
            TestCases.test_script as test_script,
            TestCases.test_case as test_case
        FROM
            Requirements
                JOIN Annotations ON vec_distance_L2(Requirements.embedding, Annotations.embedding) <= ?
                JOIN CasesToAnnos ON Annotations.id = CasesToAnnos.annotation_id
                JOIN TestCases ON TestCases.id = CasesToAnnos.case_id
        WHERE Requirements.id = ?
        ORDER BY
            Requirements.id, TestCases.id
        LIMIT ?
        """
    return db.conn.execute(sql, (radius, requirement_id, limit)).fetchall()
