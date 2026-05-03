from __future__ import annotations

from src.application.contracts import TableKey
from src.application.contracts import all_table_keys
from src.ingestion import TableInput
from src.session import AppSession


class TableInputFactory:
    @staticmethod
    def build_for_tables(
        session: AppSession,
        table_keys: tuple[TableKey, ...] = all_table_keys(),
    ) -> list[TableInput]:
        inputs: list[TableInput] = []

        for table_key in table_keys:
            table = session.get_table(table_key)
            if not table.file_path:
                continue

            inputs.append(
                TableInput(
                    table_key=table_key,
                    file_path=table.file_path,
                    sheet_name=table.sheet_name,
                    mapping=dict(table.column_mapping),
                    column_signature=list(table.column_signature),
                )
            )

        return inputs