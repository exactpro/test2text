import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go

from sklearn.manifold import TSNE
from test2text.services.utils.sqlite_vec import unpack_float32
from test2text.services.db import DbClient

FIG_SIZE = (8, 6)
FONT_SIZE = 18
DOT_SIZE_2D = 20
DOT_SIZE_3D = 10


def extract_annotation_vectors(db: DbClient):
    vectors = []
    embeddings = db.conn.execute("SELECT embedding FROM Annotations")
    if embeddings.fetchone() is None:
        st.error("Embeddings is empty. Please fill embeddings in annotations.")
        return None
    for row in embeddings.fetchall():
        if row[0] is not None:
            vectors.append(np.array(unpack_float32(row[0])))
    return np.array(vectors)


def extract_closest_annotation_vectors(db: DbClient):
    vectors = []
    embeddings = db.conn.execute("""
    SELECT embedding FROM Annotations
    WHERE id IN (
    SELECT DISTINCT annotation_id FROM AnnotationsToRequirements
    )
    """)
    if embeddings.fetchone() is None:
        st.error("Embeddings is empty. Please calculate and cache distances.")
        return None
    for row in embeddings.fetchall():
        vectors.append(np.array(unpack_float32(row[0])))
    return np.array(vectors)


def extract_requirement_vectors(db: DbClient):
    vectors = []
    embeddings = db.conn.execute("SELECT embedding FROM Requirements")
    if embeddings.fetchone() is None:
        st.error("Embeddings is empty. Please fill embeddings in requirements.")
        return None
    for row in embeddings.fetchall():
        vectors.append(np.array(unpack_float32(row[0])))
    return np.array(vectors)


def minifold_vectors_2d(vectors: np.array):
    tsne = TSNE(n_components=2, random_state=0)
    vectors_2d = tsne.fit_transform(vectors)
    return vectors_2d


def minifold_vectors_3d(vectors: np.array):
    tsne = TSNE(n_components=3, random_state=0)
    vectors_3d = tsne.fit_transform(vectors)
    return vectors_3d


def plot_vectors_2d(vectors_2d: np.array):
    fig = px.scatter(x=vectors_2d[:, 0], y=vectors_2d[:, 1])
    st.plotly_chart(fig, use_container_width=True)


def plot_vectors_3d(vectors_3d: np.array):
    fig = px.scatter_3d({"x": vectors_3d[:, 0],
                         "y": vectors_3d[:, 1],
                         "z": vectors_3d[:, 2]}, color="z")
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    st.header("Visualizing vectors")
    db = DbClient("./private/requirements.db")
    Req_tab, Anno_tab, Req_Anno_tab = st.tabs(["Requirements", "Annotations", "Requirements vs Annotations"])
    with Req_tab:
        st.subheader("Requirements vectors")
        progress_bar = st.progress(0)

        requirement_vectors = extract_requirement_vectors(db)
        progress_bar.progress(20, "Extracted")
        reqs_vectors_2d = minifold_vectors_2d(requirement_vectors)
        progress_bar.progress(40, "Minifolded for 2D")
        plot_vectors_2d(reqs_vectors_2d)
        progress_bar.progress(60, "Plotted in 2D")
        reqs_vectors_3d = minifold_vectors_3d(requirement_vectors)
        progress_bar.progress(80, "Minifolded for 3D")
        plot_vectors_3d(reqs_vectors_3d)
        progress_bar.progress(100, "Plotted in 3D")

    with Anno_tab:
        st.subheader("Annotations vectors")
        progress_bar = st.progress(0)

        annotation_vectors = extract_annotation_vectors(db)
        progress_bar.progress(20, "Extracted")
        anno_vectors_2d = minifold_vectors_2d(annotation_vectors)
        progress_bar.progress(40, "Minifolded for 2D")
        plot_vectors_2d(anno_vectors_2d)
        progress_bar.progress(60, "Plotted in 2D")
        anno_vectors_3d = minifold_vectors_3d(annotation_vectors)
        progress_bar.progress(80, "Minifolded for 3D")
        plot_vectors_3d(anno_vectors_3d)
        progress_bar.progress(100, "Plotted in 3D")

    with Req_Anno_tab:
        # Show how these 2 groups of vectors are different
        st.subheader("Requirements vs Annotations")
        progress_bar = st.progress(40, "Extracted")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=reqs_vectors_2d[:, 0], y=reqs_vectors_2d[:, 1], mode='markers', name='Requirements'))
        fig.add_trace(go.Scatter(x=anno_vectors_2d[:, 0], y=anno_vectors_2d[:, 1], mode='markers', name='Annotations'))
        fig.update_layout(title='Requirements vs Annotations', xaxis_title='X', yaxis_title='Y')
        st.plotly_chart(fig)
        progress_bar.progress(60, "Plotted in 2D")

        st.subheader("Requirements vs Annotations")
        fig = go.Figure()
        for i in range(reqs_vectors_3d.shape[0]):
            fig.add_trace(go.Scatter3d(
                x=reqs_vectors_3d[i, :, 0],
                y=reqs_vectors_3d[i, :, 1],
                z=reqs_vectors_3d[i, :, 2],
                mode='markers',
                name=f'Массив 1 — Кривая {i + 1}'
            ))
        for j in range(anno_vectors_3d.shape[0]):
            fig.add_trace(go.Scatter3d(
                x=anno_vectors_3d[j, :, 0],
                y=anno_vectors_3d[j, :, 1],
                z=anno_vectors_3d[j, :, 2],
                mode='markers',
                name=f'Массив 2 — Кривая {j + 1}',
                line=dict(dash='dash')
            ))

        fig.update_layout(
            title='Requirements vs Annotations',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z'
            )
        )
        st.plotly_chart(fig)
        progress_bar.progress(80, "Plotted in 3D")

        anno_vectors_2d = minifold_vectors_2d(extract_closest_annotation_vectors(db))
        st.subheader("Requirements vs Annotations")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=reqs_vectors_2d[:, 0], y=reqs_vectors_2d[:, 1], mode='lines', name='Requirements'))
        fig.add_trace(go.Scatter(x=anno_vectors_2d[:, 0], y=anno_vectors_2d[:, 1], mode='lines', name='Annotations'))
        fig.update_layout(title='Requirements vs Annotations', xaxis_title='X', yaxis_title='Y')
        st.plotly_chart(fig)
        progress_bar.progress(100, "Minifolded and Plotted in 2D")



