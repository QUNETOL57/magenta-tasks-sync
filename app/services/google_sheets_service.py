import re
from datetime import datetime
import time
from typing import Optional, Any

import gspread
from gspread.utils import ValueInputOption
from gspread.exceptions import APIError

from app.helpers.string_helper import extract_dates
from app.task_dto import TaskDTO
from config import config
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.enums.column_enum import ColumnEnum
from logging_config import logger


class GoogleSheetsService:
    def __init__(self):
        self.task_key = None
        self.sheet = None
        self.worksheet = None
        self.header = None
        self._cached_keys = None
        self._cache_timestamp = 0
        self._cache_duration = 30  # кэш на 30 секунд
        self._last_request_time = 0
        self._min_request_interval = 1.0  # минимум 1 секунда между запросами
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
            self.header = self._get_header()
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
            col_values = self._get_cached_keys()  # Получаем значения первого столбца с кэшированием
            for line_number, value in enumerate(col_values, start=2):
                if not value:
                    return line_number
            return len(col_values) + 1
        except Exception as e:
            logger.error(f"{self.task_key} | Error finding empty row: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def _find_task_row_by_prefix(self, prefix: str) -> Optional[int]:
        self._ensure_connection()
        try:
            self._rate_limit()
            pattern = re.compile(f'{prefix}: .+', re.IGNORECASE)
            cell = self.worksheet.find(pattern, in_column=1)
            if cell:
                return cell.row
            return None
        except Exception as e:
            logger.error(f"{self.task_key} | Error finding task row: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def _get_header(self) -> Optional[list]:
        self._ensure_connection()
        try:
            self._rate_limit()
            headers = self.worksheet.row_values(1)
            # Ищем ключ, который начинается с "Текущий спринт" значение может быть "Текущий спринт (461/1804)"
            # Для того, что бы взять его индекс и заменить на "Текущий спринт"
            sprint_index = next(
                (i for i, header in enumerate(headers) if header.startswith("Текущий спринт")),
                None  # если не найдено
            )
            headers[sprint_index] = "Текущий спринт"
            return headers
        except Exception as e:
            logger.error(f"{self.task_key} | Error finding header row: {e}")
            return None

    def store_task(self, task: TaskDTO):
        """
        Обычное сохранение задачи в Google Sheets.
        """
        try:
            self.task_key = task.key
            self._ensure_connection()
            row = self._find_task_row_by_prefix(task.key)
            if row is not None:
                self.update_task(task, row)
                logger.info(f"{self.task_key} | Updated task {task.key} at row {row}")
            else:
                self.create_task(task)
                logger.info(f"{self.task_key} | Created new task {task.key}")
        except APIError as e:
            logger.error(f"{self.task_key} | Google Sheets API Error: {e}")
            # Переинициализация соединения при API ошибке
            self.sheet = None
            self.worksheet = None
            raise
        except Exception as e:
            logger.error(f"{self.task_key} | Unexpected error storing task: {e}")
            raise

    def store_tasks_batch(self, tasks: list[TaskDTO]):
        """
        Пакетное сохранение задач в Google Sheets.
        Обновляет существующие задачи и добавляет новые за одну операцию.
        """
        self._ensure_connection()
        # Получаем все значения первого столбца (ключи задач) с кэшированием
        all_keys = self._get_cached_keys()
        # Сопоставляем ключ -> номер строки
        key_to_row = {}
        # Ставим start=1, чтобы строки начинались с 1 (в google sheets строки начинаются с 1)
        for idx, value in enumerate(all_keys, start=1):
            if value:
                prefix = value.split(":")[0]
                key_to_row[prefix] = idx

        # Готовим данные для обновления и создания
        updates = []
        creates = []
        for task in tasks:
            row = key_to_row.get(task.key)
            if row:
                try:
                    old_task_list = self.worksheet.get(f"A{row}:AM{row}")[0]
                except Exception:
                    old_task_list = ['' for _ in range(50)]
                task_list = self.mapping(task, old_task_list)
                updates.append((task.key, row, task_list))
            else:
                creates.append((task.key, task))

        # Пакетное обновление существующих задач
        if updates:
            self._batch_update_rows(updates)

        # Пакетное создание новых задач (в конец таблицы)
        if creates:
            first_empty_row = len(all_keys) + 1
            self._batch_create_rows(creates, first_empty_row)
        
        # Очищаем кэш после успешного обновления, чтобы данные были актуальными
        if updates or creates:
            self.clear_cache()

    def _batch_create_rows(self, creates: list[tuple[str, TaskDTO]], first_empty_row: int):
        """
        Пакетное добавление строк в Google Sheets.
        creates: список кортежей (task_key, task_dto)
        """

        create_rows = []
        for task_key, task in creates:
            task_list = self.mapping(task)
            create_rows.append(task_list)
        
        self._rate_limit()
        self.worksheet.update(f"A{first_empty_row}", create_rows, value_input_option=ValueInputOption.user_entered)

        row = first_empty_row
        for task_key, _ in creates:
            logger.info(f"{task_key} | Created new task {task_key} at row {row}" )
            row += 1

    def _batch_update_rows(self, updates: list[tuple[str, int, list]]):
        """
        Пакетное обновление строк в Google Sheets.
        updates: список кортежей (task_key, row_number, values_list)
        """
        requests = []
        for _, row, values in updates:
            range_a1 = f"A{row}"
            requests.append({
                "range": range_a1,
                "values": [values]
            })
        
        self._rate_limit()
        self.worksheet.batch_update(requests, value_input_option=ValueInputOption.user_entered)

        for task_key, row, _ in updates:
            logger.info(f"{task_key} | Updated task {task_key} at row {row}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((APIError, ConnectionError, TimeoutError))
    )
    def create_task(self, task: TaskDTO):
        self._ensure_connection()
        row = self._find_first_empty_row()
        task_list = self.mapping(task)
        self._rate_limit()
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
                raise ValueError(f"{self.task_key} | Task {task.key} not found")

        try:
            self._rate_limit()
            old_task_list = self.worksheet.get(f"A{row}:AM{row}")[0]
        except IndexError:
            # Если строка пустая, создаем пустой список
            old_task_list = ['' for _ in range(12)]

        task_list = self.mapping(task, old_task_list)
        self._rate_limit()
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
        result = {}
        for i, value in enumerate(data):
            key = self.header[i] if i < len(self.header) else str(i)
            result[key] = value
        return result

    @staticmethod
    def is_current_date_in_sprint(sprint: str) -> bool:
        dates = extract_dates(sprint)
        if not dates:
            return False

        start_date, end_date = dates
        today = datetime.now().date()
        return start_date <= today <= end_date

    def _rate_limit(self):
        """Ограничивает частоту запросов к API"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _get_cached_keys(self):
        """Получает ключи с кэшированием"""
        current_time = time.time()
        if (self._cached_keys is None or 
            current_time - self._cache_timestamp > self._cache_duration):
            
            self._rate_limit()
            self._cached_keys = self.worksheet.col_values(1)
            self._cache_timestamp = current_time
            logger.debug("Refreshed cached keys from Google Sheets")
        
        return self._cached_keys

    def clear_cache(self):
        """Очищает кэш ключей"""
        self._cached_keys = None
        self._cache_timestamp = 0
        logger.debug("Cleared cached keys")
