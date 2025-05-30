from datetime import datetime
import re


def extract_dates(sprint_str: str) -> tuple[datetime.date, datetime.date] | None:
    # Разбираем шаблон "(01.01 – 02.02)"
    match = re.search(r"\((\d{1,2}\.\d{1,2})\s*–\s*(\d{1,2}\.\d{1,2})\)", sprint_str)
    if not match:
        return None

    start_date_str, end_date_str = match.groups()
    # Текущий год подставляется по умолчанию
    current_year = datetime.now().year
    start_date = datetime.strptime(f"{start_date_str}.{current_year}", "%d.%m.%Y").date()
    end_date = datetime.strptime(f"{end_date_str}.{current_year}", "%d.%m.%Y").date()

    return start_date, end_date
