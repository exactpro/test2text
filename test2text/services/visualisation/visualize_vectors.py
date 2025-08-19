import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go

from sklearn.manifold import TSNE
from test2text.services.utils.sqlite_vec import unpack_float32
from test2text.services.db import DbClient, get_db_client

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
    """
    Reduces high-dimensional vectors to 2D using TSNE.
    Handles cases where the number of samples is too small for TSNE by returning the input as-is.
    """
    n_samples = vectors.shape[0]
    # TSNE requires perplexity < n_samples
    if n_samples < 2:
        return vectors.reshape(n_samples, -1)[:, :2]
    perplexity = min(30, max(1, (n_samples - 1) // 3))
    tsne = TSNE(n_components=2, random_state=0, perplexity=perplexity)
    vectors_2d = tsne.fit_transform(vectors)
    return vectors_2d


def minifold_vectors_3d(vectors: np.array):
    n_samples = vectors.shape[0]
    # TSNE requires perplexity < n_samples
    if n_samples < 2:
        return vectors.reshape(n_samples, -1)[:, :3]
    perplexity = min(30, n_samples - 1) if n_samples > 1 else 1
    tsne = TSNE(n_components=3, random_state=0, perplexity=perplexity)
    vectors_3d = tsne.fit_transform(vectors)
    return vectors_3d


def plot_vectors_2d(vectors_2d: np.array, title):
    fig = px.scatter(x=vectors_2d[:, 0], y=vectors_2d[:, 1])
    fig.update_layout(title=title, xaxis_title="X", yaxis_title="Y")
    st.plotly_chart(fig, use_container_width=True)


def plot_vectors_3d(vectors_3d: np.array, title):
    fig = px.scatter_3d(
        x=vectors_3d[:, 0],
        y=vectors_3d[:, 1],
        z=vectors_3d[:, 2],
        color=vectors_3d[:, 2],
    )
    fig.update_layout(title=title, xaxis_title="X", yaxis_title="Y")
    st.plotly_chart(fig, use_container_width=True)


def plot_2_sets_in_one_2d(
        first_set_of_vec, second_set_of_vec, first_title, second_title, first_color="blue", second_color="green"
):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=first_set_of_vec[:, 0],
            y=first_set_of_vec[:, 1],
            mode='markers',
            name=first_title,
            marker=dict(
                color=f"{first_color}"
            )
        )
    )
    fig.add_trace(
        go.Scatter(
            x=second_set_of_vec[:, 0],
            y=second_set_of_vec[:, 1],
            mode='markers',
            name=second_title,
            marker=dict(
                color=f"{second_color}"
            )
        )
    )
    fig.update_layout(
        title=f"{first_title} vs {second_title}",
        xaxis_title='X',
        yaxis_title='Y'
    )
    st.plotly_chart(fig)


def plot_2_sets_in_one_3d(
    first_set_of_vec, second_set_of_vec, first_title, second_title
):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter3d(
            x=first_set_of_vec[:, 0],
            y=first_set_of_vec[:, 1],
            z=first_set_of_vec[:, 2],
            mode="markers",
            name=first_title,
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=second_set_of_vec[:, 0],
            y=second_set_of_vec[:, 1],
            z=second_set_of_vec[:, 2],
            mode="markers",
            name=second_title,
        )
    )

    fig.update_layout(
        title=f"{first_title} vs {second_title}",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
        ),
    )
    st.plotly_chart(fig)


def visualize_vectors():
    st.header("Visualizing vectors")
    db = get_db_client()
    Req_tab, Anno_tab, Req_Anno_tab = st.tabs(
        ["Requirements", "Annotations", "Requirements vs Annotations"]
    )
    with Req_tab:
        st.subheader("Requirements vectors")
        progress_bar = st.progress(0)

        requirement_vectors = extract_requirement_vectors(db)
        progress_bar.progress(20, "Extracted")
        reqs_vectors_2d = minifold_vectors_2d(requirement_vectors)
        progress_bar.progress(40, "Minifolded for 2D")
        plot_vectors_2d(reqs_vectors_2d, "Requirements")
        progress_bar.progress(60, "Plotted in 2D")
        reqs_vectors_3d = minifold_vectors_3d(requirement_vectors)
        progress_bar.progress(80, "Minifolded for 3D")
        plot_vectors_3d(reqs_vectors_3d, "Requirements")
        progress_bar.progress(100, "Plotted in 3D")

    with Anno_tab:
        st.subheader("Annotations vectors")
        progress_bar = st.progress(0)

        annotation_vectors = extract_annotation_vectors(db)
        progress_bar.progress(20, "Extracted")
        anno_vectors_2d = minifold_vectors_2d(annotation_vectors)
        progress_bar.progress(40, "Minifolded for 2D")
        plot_vectors_2d(anno_vectors_2d, "Annotations")
        progress_bar.progress(60, "Plotted in 2D")
        anno_vectors_3d = minifold_vectors_3d(annotation_vectors)
        progress_bar.progress(80, "Minifolded for 3D")
        plot_vectors_3d(anno_vectors_3d, "Annotations")
        progress_bar.progress(100, "Plotted in 3D")

    with Req_Anno_tab:
        # Show how these 2 groups of vectors are different
        st.subheader("Requirements vs Annotations")
        progress_bar = st.progress(40, "Extracted")
        plot_2_sets_in_one_2d(
            reqs_vectors_2d, anno_vectors_2d, "Requerements", "Annotations"
        )
        progress_bar.progress(60, "Plotted in 2D")

        plot_2_sets_in_one_3d(
            reqs_vectors_3d, anno_vectors_3d, "Requerements", "Annotations"
        )
        progress_bar.progress(80, "Plotted in 3D")

        anno_vectors_2d = minifold_vectors_2d(extract_closest_annotation_vectors(db))

        plot_2_sets_in_one_2d(
            reqs_vectors_2d, anno_vectors_2d, "Requerements", "Annotations"
        )
        progress_bar.progress(100, "Minifolded and Plotted in 2D")
    db.conn.close()


if __name__ == "__main__":
    visualize_vectors()
