from abc import ABC, abstractmethod

from pandas import DataFrame


class TableParser(ABC):
    def __init__(self, columns: dict[str, str]):
        self._cols = columns

    @abstractmethod
    def parse(self, df: DataFrame):
        pass

    def get_filtered_competition_cols(self, df: DataFrame) -> set:
        prefix = self._cols["assignment_prefix"]
        filtered_competition_cols = set()
        if prefix == "":
            for col in df.columns:
                temp = str(col).strip()
                for i, char in enumerate(temp):
                    if not char.isdigit():
                        break
                    elif i == len(temp) - 1:
                        filtered_competition_cols.add(col)
        else:
            filtered_competition_cols.update(c for c in df.columns if str(c).startswith(prefix))
        return filtered_competition_cols
