from test2text.services.db import DbClient


def fetch_test_cases_by_requirement(
    db: DbClient, requirement_id: int, radius: float, limit: int
) -> list:
    sql = f"""
        SELECT
            Requirements.id as req_id,
            Requirements.external_id as req_external_id,
            Requirements.summary as req_summary,
            Requirements.embedding as req_embedding,

            Annotations.id as anno_id,
            Annotations.summary as anno_summary,
            Annotations.embedding as anno_embedding,

            vec_distance_L2(Requirements.embedding, Annotations.embedding) as distance,

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
            Requirements.id, distance, TestCases.id
        LIMIT ?
        """
    return db.conn.execute(sql, (radius, requirement_id, limit)).fetchall()
