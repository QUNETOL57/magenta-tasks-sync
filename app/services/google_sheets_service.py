import gspread
from gspread.utils import ValueInputOption

from app.task_dto import TaskDTO
from config import config


class GoogleSheetsService:
    def __init__(self):
        gc = gspread.service_account(filename='credentials/google.json')
        self.sheet = gc.open_by_key(config.get('GOOGLE_SHEET_KEY'))
        self.worksheet = self.sheet.worksheet(config.get('GOOGLE_SHEET_WORKSHEET'))

    def _find_first_empty_row(self) -> int:
        col_values = self.worksheet.col_values(1)
        for line_number, value in enumerate(col_values, start=1):
            # пропускаем строку с заголовками (2)
            if not value and line_number != 2:
                return line_number
        return len(col_values) + 1

    def add_task(self, task: TaskDTO):
        first_empty_row = self._find_first_empty_row()
        hyperlink = f'=HYPERLINK("{task.url()}"; "{task.name()}")'
        off_the_plan = bool(task.off_the_plan)
        moving_on_to_the_next_sprint = bool(task.moving_on_to_the_next_sprint)
        self.worksheet.update([[hyperlink, '', task.assignee, '', '', task.status, task.due_date, off_the_plan, '', '',
                                moving_on_to_the_next_sprint]],
                              f"A{first_empty_row}", value_input_option=ValueInputOption.user_entered)
        # TODO реализовать получение столбца исполнителя
        user_column = "Q"
        self.worksheet.update([[task.sp_development]], f"{user_column}{first_empty_row}",
                              value_input_option=ValueInputOption.user_entered)
