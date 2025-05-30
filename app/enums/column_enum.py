import enum

class ColumnEnum(enum.Enum):
    name = "Наименование"
    assignee = "Исполнитель"
    type = "Type"
    sprint = "Текущий спринт"
    status = "Статус"
    stage_deadline = "Дедлайн этапа"
    due_date = "Дедлайн"
    deadline_fact = "Дедлайн факт"
    project = "Проект"
    priority = "Приоритет"
    off_the_plan = "Вне плана? (бизнес)"
    outside_of_the_sprint_plan = "Вне плана Спринта?"
    moving_on_to_the_next_sprint = "Переход на след. спринт?"
    comment = "Комментарии"
    sp = "Общая оценка SP"
    igr = "IGR & Done\nобщий"

