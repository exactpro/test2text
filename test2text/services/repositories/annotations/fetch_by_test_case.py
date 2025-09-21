from test2text.services.db import DbClient


def fetch_annotations_by_test_case(
    db: DbClient, test_case_id: int
) -> list[tuple[int, str, bytes]]:
    sql = """
        SELECT
            Annotations.id as anno_id,
            Annotations.summary as anno_summary,
            Annotations.embedding as anno_embedding
        FROM
            Annotations
                JOIN CasesToAnnos ON Annotations.id = CasesToAnnos.annotation_id
        WHERE CasesToAnnos.case_id = ?
        """
    return db.conn.execute(sql, (test_case_id,)).fetchall()


def fetch_annotations_by_test_case_with_distance_to_requirement(
    db: DbClient, test_case_id: int, requirement_embedding: bytes
) -> list[tuple[int, str, bytes, float]]:
    sql = """
        SELECT
            Annotations.id as anno_id,
            Annotations.summary as anno_summary,
            Annotations.embedding as anno_embedding,
            vec_distance_L2(?, Annotations.embedding) as distance
        FROM
            Annotations
                JOIN CasesToAnnos ON Annotations.id = CasesToAnnos.annotation_id
        WHERE CasesToAnnos.case_id = ?
        ORDER BY
            distance ASC
        """
    return db.conn.execute(sql, (requirement_embedding, test_case_id)).fetchall()
