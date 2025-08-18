from string import Template

import streamlit as st


def show_requirements():
    with st.form("upload_requirements_form"):
        st.title("Upload a file with requirements")

        uploaded_files = st.file_uploader(
            "Choose a file with requirements", type="csv", accept_multiple_files=True
        )

        if not uploaded_files:
            st.info("Please upload a *.trace.csv file to extract rows.")

        submitted = st.form_submit_button("Upload")

    if submitted:
        try:
            with st.spinner("Loading requirements...", show_time=True):
                current_file_no = 0
                current_file_name = ""
                processed_requirement = 0

                alert_template = Template(
                    "Processing file $file_no: $file_name. Annotations processed so far: $processed_requirement."
                )
                alert = st.info("Embedding model is initializing...")

                def on_start_file(file_no: int, file_name: str):
                    nonlocal current_file_no, current_file_name
                    current_file_no = file_no
                    current_file_name = file_name
                    alert.info(
                        alert_template.substitute(
                            file_no=current_file_no,
                            file_name=current_file_name,
                            processed_requirement=processed_requirement,
                        )
                    )

                def on_requirement_written(external_id: str):
                    nonlocal processed_requirement
                    processed_requirement += 1
                    alert.info(
                        alert_template.substitute(
                            file_no=current_file_no,
                            file_name=current_file_name,
                            processed_requirement=processed_requirement,
                        )
                    )

                from test2text.services.loaders.index_requirements import (
                    index_requirements_from_files,
                )

                index_requirements_from_files(
                    uploaded_files,
                    on_start_file=on_start_file,
                    on_requirement_written=on_requirement_written,
                )
        except ValueError as e:
            st.error(str(e))
            return
        st.success("CSV file uploaded successfully! Requirements indexed.")


if __name__ == "__main__":
    show_requirements()
