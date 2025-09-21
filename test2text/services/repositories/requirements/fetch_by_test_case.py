from test2text.services.db import DbClient


def fetch_requirements_by_test_case(
    db: DbClient, *, test_case_id: int, radius: float, limit: int
) -> list[tuple[int, str, str]]:
    sql = """
        SELECT DISTINCT 
            Requirements.id as req_id,
            Requirements.external_id as req_external_id,
            Requirements.summary as req_summary,
            MIN(vec_distance_L2(Requirements.embedding, Annotations.embedding)) as min_distance
        FROM
            TestCases
                JOIN CasesToAnnos ON TestCases.id = CasesToAnnos.case_id
                JOIN Annotations ON Annotations.id = CasesToAnnos.annotation_id
                JOIN Requirements ON vec_distance_L2(Requirements.embedding, Annotations.embedding) <= ?
        WHERE TestCases.id = ?
        GROUP BY Requirements.id
        ORDER BY
            min_distance
        LIMIT ?
    """
    return db.conn.execute(sql, (test_case_id, radius, limit)).fetchall()
