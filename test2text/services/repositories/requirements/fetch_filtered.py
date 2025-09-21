from typing import Optional

from sqlite_vec import serialize_float32

from test2text.services.db import DbClient


def fetch_filtered_requirements(db: DbClient,
                                *_,
                                external_id: Optional[str] = None,
                                text_content: Optional[str] = None,
                                smart_search_query: Optional[str] = None) -> list[tuple[int, str, str]]:
    sql = f"""
            SELECT
                Requirements.id as req_id,
                Requirements.external_id as req_external_id,
                Requirements.summary as req_summary
            FROM
                Requirements
            """
    options = []
    if external_id or text_content or smart_search_query:
        sql += " WHERE "
        conditions = []
        if external_id:
            conditions.append("Requirements.external_id LIKE ?")
            options.append(f"%{external_id.strip()}%")
        if text_content:
            conditions.append("Requirements.summary LIKE ?")
            options.append(f"%{text_content.strip()}%")
        if smart_search_query:
            from test2text.services.embeddings.embed import embed_requirement
            embedding = embed_requirement(smart_search_query.strip())
            conditions.append("vec_distance_L2(Requirements.embedding, ?) < 0.7")
            options.append(serialize_float32(embedding))
        sql += " AND ".join(conditions)
    sql += " ORDER BY Requirements.id ASC"


    return db.conn.execute(sql, options).fetchall()
