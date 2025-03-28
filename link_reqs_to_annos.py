import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
from test2text.db import DbClient

if __name__ == '__main__':
    db = DbClient('./private/requirements.db')
    db.annos_to_reqs.recreate_table()
    # Link requirements to annotations
    annotations = db.conn.execute("""
    SELECT 
        Annotations.id AS anno_id,
        Requirements.id AS req_id,
        vec_distance_L2(Annotations.embedding, Requirements.embedding) AS distance
    FROM Annotations, Requirements
    ORDER BY req_id, distance
    """)
    # Visualize distances
    distances = []
    logger.info('Processing distances')
    current_req_id = None
    current_req_annos = 0
    for i, (anno_id, req_id, distance) in enumerate(annotations.fetchall()):
        distances.append(distance)
        if req_id != current_req_id:
            current_req_id = req_id
            current_req_annos = 0
        if current_req_annos < 5 or distance < 0.7:
            db.annos_to_reqs.insert(annotation_id=anno_id, requirement_id=req_id, cached_distance=distance)
            current_req_annos += 1
    db.conn.commit()
    import matplotlib.pyplot as plt
    plt.hist(distances, bins=100)
    plt.savefig('./private/distances.png')