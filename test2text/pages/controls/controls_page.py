from test2text.services.db import get_db_client


def controls_page():
    import streamlit as st
    import plotly.express as px

    st.header("Controls page")
    embedding_col, distances_col = st.columns(2)
    with embedding_col:
        st.subheader("Embedding")

        def refresh_counts():
            with get_db_client() as db:
                st.session_state["all_annotations_count"] = db.annotations.count
                st.session_state["embedded_annotations_count"] = (
                    db.count_notnull_entries("embedding", from_table="Annotations")
                )

        refresh_counts()

        st.write("Annotations count: ", st.session_state["all_annotations_count"])
        st.write(
            "Annotations with embeddings: ",
            st.session_state["embedded_annotations_count"],
        )

        embed_all = st.checkbox("Overwrite existing embeddings", value=False)
        embed_btn = st.button("Start embedding annotations")

        if embed_btn:
            progress_bar = st.progress(0, "Embedding annotations...")

            def update_progress(progress: float):
                progress_bar.progress(progress, "Embedding annotations...")

            from test2text.services.embeddings.annotation_embeddings_controls import (
                embed_annotations,
            )

            embed_annotations(embed_all=embed_all, on_progress=update_progress)
            refresh_counts()
            st.success("Annotations embedded successfully")

    with distances_col:
        st.subheader("Distances")

        if st.button("Refresh distances"):
            with st.spinner("Refreshing distances", show_time=True):
                from test2text.services.embeddings.cache_distances import (
                    refresh_and_get_distances,
                )

                distances = refresh_and_get_distances()
                st.success("Distances refreshed successfully")

                fig = px.histogram(distances, nbins=100, title="Distances histogram")
                st.plotly_chart(fig)
