import numpy as np
import matplotlib.pyplot as plt
import logging
logging.basicConfig(level=logging.DEBUG)
from sklearn.manifold import TSNE
from test2text.utils.sqlite_vec import unpack_float32
from test2text.db import DbClient

FIG_SIZE = (8, 6)
FONT_SIZE = 18
DOT_SIZE_2D = 20
DOT_SIZE_3D = 10

def extract_annotation_vectors(db: DbClient):
    vectors = []
    for row in db.conn.execute("SELECT embedding FROM Annotations").fetchall():
        vectors.append(np.array(unpack_float32(row[0])))
    return np.array(vectors)

def extract_requirement_vectors(db: DbClient):
    vectors = []
    for row in db.conn.execute("SELECT embedding FROM Requirements").fetchall():
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

def plot_vectors_2d(vectors_2d: np.array, title: str):
    plt.figure(figsize=FIG_SIZE)
    plt.scatter(vectors_2d[:, 0], vectors_2d[:, 1], alpha=0.7, s=DOT_SIZE_2D)
    plt.title(title)
    plt.grid(True)
    plt.savefig(f'./private/{title} vectors 2d.png')

def plot_vectors_3d(vectors_3d: np.array, title: str):
    fig = plt.figure(figsize=FIG_SIZE)
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(vectors_3d[:, 0], vectors_3d[:, 1], vectors_3d[:, 2], alpha=0.7, s=DOT_SIZE_3D)
    plt.title(title)
    plt.grid(True)
    plt.savefig(f'./private/{title} vectors 3d.png')

if __name__ == "__main__":
    logging.info('Visualizing vectors')
    db = DbClient("./private/requirements.db")
    logging.info('Database connected')

    requirement_vectors = extract_requirement_vectors(db)
    logging.info('Requirement vectors extracted')
    reqs_vectors_2d = minifold_vectors_2d(requirement_vectors)
    logging.info('Requirement vectors 2d minifolded')
    plot_vectors_2d(reqs_vectors_2d, 'Requirements')
    logging.info('Requirement vectors 2d plotted')
    reqs_vectors_3d = minifold_vectors_3d(requirement_vectors)
    logging.info('Requirement vectors 3d minifolded')
    plot_vectors_3d(reqs_vectors_3d, 'Requirements')
    logging.info('Requirement vectors 3d plotted')

    annotation_vectors = extract_annotation_vectors(db)
    logging.info('Annotation vectors extracted')
    anno_vectors_2d = minifold_vectors_2d(annotation_vectors)
    logging.info('Annotation vectors 2d minifolded')
    plot_vectors_2d(anno_vectors_2d, 'Annotations')
    logging.info('Annotation vectors 2d plotted')
    anno_vectors_3d = minifold_vectors_3d(annotation_vectors)
    logging.info('Annotation vectors 3d minifolded')
    plot_vectors_3d(anno_vectors_3d, 'Annotations')
    logging.info('Annotation vectors 3d plotted')

    # Show how these 2 groups of vectors are different
    plt.figure(figsize=FIG_SIZE)
    plt.scatter(reqs_vectors_2d[:, 0], reqs_vectors_2d[:, 1], alpha=0.5, s=DOT_SIZE_2D, label='Requirements')
    plt.scatter(anno_vectors_2d[:, 0], anno_vectors_2d[:, 1], alpha=0.5, s=DOT_SIZE_2D, label='Annotations')
    plt.title('Requirements vs Annotations')
    plt.legend(fontsize=FONT_SIZE)
    plt.grid(True)
    plt.savefig(f'./private/Requirements vs Annotations vectors 2d.png')

    fig = plt.figure(figsize=FIG_SIZE)
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(reqs_vectors_3d[:, 0], reqs_vectors_3d[:, 1], reqs_vectors_3d[:, 2], alpha=0.5, s=DOT_SIZE_3D, label='Requirements')
    ax.scatter(anno_vectors_3d[:, 0], anno_vectors_3d[:, 1], anno_vectors_3d[:, 2], alpha=0.5, s=DOT_SIZE_3D, label='Annotations')
    plt.title('Requirements vs Annotations')
    plt.legend(fontsize=FONT_SIZE)
    plt.grid(True)
    plt.savefig(f'./private/Requirements vs Annotations vectors 3d.png')