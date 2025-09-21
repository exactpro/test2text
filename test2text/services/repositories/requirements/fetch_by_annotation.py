from test2text.services.db import DbClient


def fetch_requirements_by_annotation(
    db: DbClient, *, annotation_id: int, radius: float, limit: int
) -> list[tuple[int, str, str, bytes, float]]:
    sql = """
        SELECT DISTINCT 
            Requirements.id as req_id,
            Requirements.external_id as req_external_id,
            Requirements.summary as req_summary,
            Requirements.embedding as req_embedding,
            vec_distance_L2(Requirements.embedding, Annotations.embedding) as distance
        FROM
            Annotations
                JOIN Requirements ON vec_distance_L2(Requirements.embedding, Annotations.embedding) <= ?
        WHERE Annotations.id = ?
        ORDER BY
            distance
        LIMIT ?
    """
    return db.conn.execute(sql, (radius, annotation_id, limit)).fetchall()
