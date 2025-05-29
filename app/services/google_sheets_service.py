import logging
import re
from typing import Optional

import gspread
from gspread.utils import ValueInputOption
from gspread.exceptions import APIError, SpreadsheetNotFound

from app.helpers.list_helper import add_alphabet_keys
from app.task_dto import TaskDTO
from config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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

    @staticmethod
    def mapping(task: TaskDTO, old_task_list=None):
        if old_task_list is None:
            old_task_list = ['' for _ in range(12)]

        # Убеждаемся, что список достаточно длинный
        while len(old_task_list) < 12:
            old_task_list.append('')

        task_list = add_alphabet_keys(old_task_list)
        task_list["A"] = task.hyperlink
        task_list["B"] = task.assignee or ""
        task_list["C"] = task.type or ""
        task_list["D"] = task_list.get("D", "")
        task_list["E"] = task.status or ""
        task_list["F"] = task.stage_deadline or ""
        task_list["G"] = task.due_date or ""
        task_list["H"] = task.priority or ""
        task_list["I"] = task.off_the_plan
        task_list["J"] = task.moving_next_sprint
        task_list["L"] = task.sp_development or ""

        return list(task_list.values())