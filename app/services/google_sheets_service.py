import re
from typing import Optional

import gspread
from gspread.utils import ValueInputOption

from app.helpers.list_helper import add_alphabet_keys
from app.task_dto import TaskDTO
from config import config


class GoogleSheetsService:
    def __init__(self):
        gc = gspread.service_account(filename='credentials/google.json')
        self.sheet = gc.open_by_key(config.get('GOOGLE_SHEET_KEY'))
        self.worksheet = self.sheet.worksheet(config.get('GOOGLE_SHEET_WORKSHEET'))

    # Поиск первой пустой строки
    def _find_first_empty_row(self) -> int:
        col_values = self.worksheet.col_values(1)
        for line_number, value in enumerate(col_values, start=1):
            # пропускаем строку с заголовками (2)
            if not value and line_number != 2:
                return line_number
        return len(col_values) + 1

    # Поиск строки по префиксу (номеру) задачи
    def _find_task_row_by_prefix(self, prefix: str) -> Optional[int]:
        pattern = re.compile(f'{prefix}: .+', re.IGNORECASE)
        cell = self.worksheet.find(pattern, in_column=1)
        if cell:
            return cell.row
        return None

    def add_task(self, task: TaskDTO):
        row = self._find_first_empty_row()
        task_list = self.mapping(task)
        self.worksheet.update([task_list], f"A{row}",
                              value_input_option=ValueInputOption.user_entered)

    def update_task(self, task: TaskDTO):
        row = self._find_task_row_by_prefix(task.key)
        if row is not None:
            old_task_list = self.worksheet.get(f"A{row}:AM{row}")[0]
            task_list = self.mapping(task, old_task_list)
            self.worksheet.update([task_list], f"A{row}",
                                  value_input_option=ValueInputOption.user_entered)
        else:
            self.add_task(task)

    @staticmethod
    def mapping(task: TaskDTO, old_task_list=None):
        if old_task_list is None:
            old_task_list = ['' for _ in range(12)]
        task_list = add_alphabet_keys(old_task_list)
        task_list["A"] = task.hyperlink
        task_list["B"] = task.assignee
        task_list["C"] = task.type
        task_list["D"] = task_list["D"]
        task_list["E"] = task.status
        task_list["F"] = task.stage_deadline
        task_list["G"] = task.due_date
        task_list["H"] = task.priority
        task_list["I"] = task.off_the_plan
        task_list["J"] = task.moving_next_sprint
        task_list["L"] = task.sp_development

        return list(task_list.values())
