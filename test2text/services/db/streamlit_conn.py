from .client import DbClient


def get_db_client() -> DbClient:
    from test2text.services.utils import res_folder

    return DbClient(res_folder.get_file_path("db.sqlite3"))
