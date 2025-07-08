from test2text.db import DbClient

if __name__ == '__main__':
    db = DbClient('./private/requirements.db')
    db.case_to_annos.init_table()
    case_to_annos = db.conn.execute("""
                    SELECT c.case_id, GROUP_CONCAT(a.summary, ", ")
                    FROM CasesToAnnos as c
                    JOIN Annotations as a ON c.annotation_id == a.id
                    GROUP BY case_id;
                """)

    for i, (case_id, annotations) in enumerate(case_to_annos.fetchall()):
        db.case_to_annos.insert(case_id=case_id, annotations=annotations)
        print(case_id, annotations)

    db.conn.commit()





