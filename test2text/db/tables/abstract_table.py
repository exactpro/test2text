from abc import ABC, abstractmethod
from sqlite3 import Connection


class AbstractTable(ABC):
    def __init__(self, connection: Connection):
        self.connection = connection

    @abstractmethod
    def init_table(self):
        pass

