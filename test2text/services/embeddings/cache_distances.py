from test2text.services.db import get_db_client


def refresh_and_get_distances() -> list[float]:
    with get_db_client() as db:
        db.annos_to_reqs.recreate_table()
        # Link requirements to annotations
        annotations = db.get_distances()
        # Visualize distances
        distances = []
        current_req_id = None
        current_req_annos = 0
        for i, (anno_id, req_id, distance) in enumerate(annotations):
            distances.append(distance)
            if req_id != current_req_id:
                current_req_id = req_id
                current_req_annos = 0
            if current_req_annos < 5 or distance < 0.7:
                db.annos_to_reqs.insert(
                    annotation_id=anno_id,
                    requirement_id=req_id,
                    cached_distance=distance,
                )
                current_req_annos += 1
        return distances


if __name__ == "__main__":
    refresh_and_get_distances()
