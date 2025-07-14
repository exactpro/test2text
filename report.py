from test2text.db import DbClient
from tqdm import tqdm


def add_new_line(summary):
    return summary.replace("\n", "<br>")


if __name__ == "__main__":
    with open("./private/report.html", "w", newline="", encoding="utf-8") as f:
        f.write("""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="../resources/typography.css">
            <title>Test2Text Report</title>
        </head>
        <body>
        <main style="padding: 1rem;">
            <article class="prose prose-sm container" 
                     style="max-width: 48rem; margin: 0 auto;">
        """)

        db = DbClient("./private/requirements.db")
        all_reqs_count = db.conn.execute(
            "SELECT COUNT(*) FROM Requirements"
        ).fetchone()[0]

        f.write('<nav style="break-after: page;"><h1>Table of Contents</h1><ul>')

        for requirement in tqdm(
            db.conn.execute("SELECT * FROM Requirements").fetchall(),
            desc="Generating table of contents",
            unit="requirements",
            total=all_reqs_count,
        ):
            req_id, req_external_id, req_summary, _ = requirement
            f.write(f"""
            <li>
                <a href="#req_{req_id}">
                    Requirement {req_external_id} ({req_id})
                </a>
            </li>""")

        f.write("</ul></nav>")

        data = db.conn.execute("""
        SELECT
            Requirements.id as req_id,
            Requirements.external_id as req_external_id,
            Requirements.summary as req_summary,
            
            Annotations.id as anno_id,
            Annotations.summary as anno_summary,
            
            AnnotationsToRequirements.cached_distance as distance,
            
            TestCases.id as case_id,
            TestCases.test_script as test_script,
            TestCases.test_case as test_case
        FROM
            Requirements
                JOIN AnnotationsToRequirements ON Requirements.id = AnnotationsToRequirements.requirement_id
                JOIN Annotations ON Annotations.id = AnnotationsToRequirements.annotation_id
                JOIN CasesToAnnos ON Annotations.id = CasesToAnnos.annotation_id
                JOIN TestCases ON TestCases.id = CasesToAnnos.case_id
        ORDER BY
            Requirements.id, AnnotationsToRequirements.cached_distance, TestCases.id
        """)

        current_req_id = None
        current_annotations = {}
        current_test_scripts = set()
        progress_bar = tqdm(
            total=all_reqs_count, desc="Generating report", unit="requirements"
        )

        written_count = 0

        def write_requirement():
            global written_count
            # if written_count > 5:
            #     return
            written_count += 1
            f.write(f"""
                                <section style="break-after: page;">
                                <h2 id="req_{current_req_id}">Requirement {current_req_external_id} ({current_req_id})</h2>
                                <p>{add_new_line(req_summary)}</p>
                                <h3>Annotations</h3>
                                <ul>
                                """)
            for anno_id, (anno_summary, distance) in current_annotations.items():
                f.write(
                    f"<li>Annotation {anno_id} (distance: {distance:.3f}): <p>{add_new_line(anno_summary)}</p></li>"
                )
            f.write("</ul>")
            f.write("<h3>Test Scripts</h3><ul>")
            for test_script in current_test_scripts:
                f.write(f"<li>{test_script}</li>")
            f.write("</ul></section>")

        for row in data.fetchall():
            (
                req_id,
                req_external_id,
                req_summary,
                anno_id,
                anno_summary,
                distance,
                case_id,
                test_script,
                test_case,
            ) = row
            if req_id != current_req_id:
                if current_req_id is not None:
                    write_requirement()
                current_req_id = req_id
                current_req_external_id = req_external_id
                current_annotations = {}
                current_test_scripts = set()
                progress_bar.update(1)
            current_annotations[anno_id] = (anno_summary, distance)
            current_test_scripts.add(test_script)
        write_requirement()
        f.write("""
        </article>
        </main>
        </body>
        </html>
        """)
