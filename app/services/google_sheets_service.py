import logging
import re
from datetime import datetime

from typing import Optional, Any

import gspread
from gspread.utils import ValueInputOption
from gspread.exceptions import APIError

from app.helpers.string_helper import extract_dates
from app.task_dto import TaskDTO
from config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.enums.column_enum import ColumnEnum

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSheetsService:
    def __init__(self):
        self.sheet = None
        self.worksheet = None
        self._initialize_connection()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def _initialize_connection(self):
        try:
            gc = gspread.service_account(filename='credentials/google.json')
            self.sheet = gc.open_by_key(config.get('GOOGLE_SHEET_KEY'))
            self.worksheet = self.sheet.worksheet(config.get('GOOGLE_SHEET_WORKSHEET'))
            logger.info("Google Sheets connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets connection: {e}")
            raise

    def _ensure_connection(self):
        """Проверяет и восстанавливает соединение при необходимости"""
        if self.sheet is None or self.worksheet is None:
            self._initialize_connection()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def _find_first_empty_row(self) -> int:
        self._ensure_connection()
        try:
            col_values = self.worksheet.col_values(1)
            for line_number, value in enumerate(col_values, start=1):
                if not value and line_number != 2:
                    return line_number
            return len(col_values) + 1
        except Exception as e:
            logger.error(f"Error finding empty row: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def _find_task_row_by_prefix(self, prefix: str) -> Optional[int]:
        self._ensure_connection()
        try:
            pattern = re.compile(f'{prefix}: .+', re.IGNORECASE)
            cell = self.worksheet.find(pattern, in_column=1)
            if cell:
                return cell.row
            return None
        except Exception as e:
            logger.error(f"Error finding task row: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def _get_header(self) -> Optional[list]:
        self._ensure_connection()
        try:
            return self.worksheet.row_values(1)
        except Exception as e:
            logger.error(f"Error finding header row: {e}")
            return None

    def store_task(self, task: TaskDTO):
        try:
            self._ensure_connection()
            row = self._find_task_row_by_prefix(task.key)
            if row is not None:
                self.update_task(task, row)
                logger.info(f"Updated task {task.key} at row {row}")
            else:
                self.create_task(task)
                logger.info(f"Created new task {task.key}")
        except APIError as e:
            logger.error(f"Google Sheets API Error: {e}")
            # Переинициализация соединения при API ошибке
            self.sheet = None
            self.worksheet = None
            raise
        except Exception as e:
            logger.error(f"Unexpected error storing task: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def create_task(self, task: TaskDTO):
        self._ensure_connection()
        row = self._find_first_empty_row()
        task_list = self.mapping(task)
        self.worksheet.update([task_list], f"A{row}",
                              value_input_option=ValueInputOption.user_entered)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def update_task(self, task: TaskDTO, row=None):
        self._ensure_connection()
        if row is None:
            row = self._find_task_row_by_prefix(task.key)
            if row is None:
                raise ValueError(f"Task {task.key} not found")

        try:
            old_task_list = self.worksheet.get(f"A{row}:AM{row}")[0]
        except IndexError:
            # Если строка пустая, создаем пустой список
            old_task_list = ['' for _ in range(12)]

        task_list = self.mapping(task, old_task_list)
        self.worksheet.update([task_list], f"A{row}",
                              value_input_option=ValueInputOption.user_entered)

    def mapping(self, task: TaskDTO, old_task_list=None) -> list[dict[str, Any]]:
        max_columns_count = 50
        if old_task_list is None:
            old_task_list = ['' for _ in range(max_columns_count)]

        # Убеждаемся, что список достаточно длинный
        while len(old_task_list) < max_columns_count:
            old_task_list.append('')

        old_task_list = self.add_columns_keys(old_task_list)
        task_list = self.add_columns_keys(['' for _ in range(max_columns_count)])

        sprint = self.is_current_date_in_sprint(task.sprint)

        task_list[ColumnEnum.name.value] = task.hyperlink
        task_list[ColumnEnum.assignee.value] = task.assignee
        task_list[ColumnEnum.type.value] = task.type or ""
        task_list[ColumnEnum.sprint.value] = sprint
        task_list[ColumnEnum.status.value] = task.status or ""
        task_list[ColumnEnum.stage_deadline.value] = task.stage_deadline or ""
        task_list[ColumnEnum.due_date.value] = task.due_date or ""
        task_list[ColumnEnum.deadline_fact.value] = task.deadline_fact or ""
        task_list[ColumnEnum.project.value] = task.project or ""
        task_list[ColumnEnum.priority.value] = task.priority or ""
        task_list[ColumnEnum.off_the_plan.value] = task.off_the_plan
        task_list[ColumnEnum.outside_of_the_sprint_plan.value] = task.outside_sprint
        task_list[ColumnEnum.moving_on_to_the_next_sprint.value] = task.moving_next_sprint
        task_list[ColumnEnum.comment.value] = old_task_list[ColumnEnum.comment.value] or ""

        if task.dev != "" and task.sp_development != "":
            task_list[task.dev] = task.sp_development

        if task.qa_engineer != "" and task.sp_testing != "":
            task_list[task.qa_engineer] = task.sp_testing

        return list(task_list.values())

    def add_columns_keys(self, data: list[Any]) -> dict[str, Any]:
        headers = self._get_header()
        # Ищем ключ, который начинается с "Текущий спринт"
        sprint_index = next(
            (i for i, header in enumerate(headers) if header.startswith("Текущий спринт")),
            None  # если не найдено
        )
        headers[sprint_index] = "Текущий спринт"

        result = {}
        for i, value in enumerate(data):
            key = headers[i] if i < len(headers) else str(i)
            result[key] = value
        return result

    def is_current_date_in_sprint(self, sprint: str) -> bool:
        dates = extract_dates(sprint)
        if not dates:
            return False

        start_date, end_date = dates
        today = datetime.now().date()
        return start_date <= today <= end_date


