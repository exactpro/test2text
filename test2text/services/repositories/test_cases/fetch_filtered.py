from typing import Optional

from sqlite_vec import serialize_float32

from test2text.services.db import DbClient


def fetch_filtered_test_cases(
    db: DbClient,
    *_,
    text_content: Optional[str] = None,
    smart_search_query: Optional[str] = None,
) -> list[tuple[int, str, str]]:
    sql = """
            SELECT
                TestCases.id as case_id,
                TestCases.test_script as test_script,
                TestCases.test_case as test_case
            FROM
                TestCases
            """
    params = []
    if text_content or smart_search_query:
        sql += " WHERE "
        conditions = []
        if text_content:
            conditions.append("TestCases.test_case LIKE ?")
            params.append(f"%{text_content.strip()}%")
        if smart_search_query:
            from test2text.services.embeddings.embed import embed_requirement

            embedding = embed_requirement(smart_search_query.strip())
            conditions.append("vec_distance_L2(TestCases.embedding, ?) < 0.7")
            params.append(serialize_float32(embedding))
        sql += " AND ".join(conditions)
    return db.conn.execute(sql, params).fetchall()
