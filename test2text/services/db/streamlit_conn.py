from .client import DbClient


def get_db_client() -> DbClient:
    """
    Returns a DbClient instance connected to the database where requirements, annotations, test cases and their relations are stored.
    :return: DbClient instance
    """
    from test2text.services.utils import res_folder

    return DbClient(res_folder.get_file_path("db.sqlite3"))
