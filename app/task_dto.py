from typing import Optional

class TaskDTO:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.key = kwargs.get("key")
        self._summary = kwargs.get("summary", "")  # Значение по умолчанию
        self.stage_deadline = kwargs.get("stageDeadline")
        self.type = kwargs.get("type")
        self.assignee = kwargs.get("assignee")
        self.status = kwargs.get("status")
        self.due_date = kwargs.get("dueDate")
        self._off_the_plan = kwargs.get("offThePlan")
        self._moving_on_to_the_next_sprint = kwargs.get("movingOnToTheNextSprint")
        self.sp_development = kwargs.get("spDevelopment")
        self.sprint = kwargs.get("sprint")
        self.priority = kwargs.get("priority")
        self.updated_by = kwargs.get("updatedBy")
        self.updated_at = kwargs.get("updatedAt")

    @property
    def off_the_plan(self):
        return bool(self._off_the_plan)

    @property
    def moving_next_sprint(self):
        return bool(self._moving_on_to_the_next_sprint)

    @property
    def summary(self):
        # Безопасная обработка None значений
        if self._summary is None:
            return ""
        return str(self._summary).replace('"', '')

    @property
    def hyperlink(self) -> str:
        return f'=HYPERLINK("{self.url()}"; "{self.name()}")'

    def url(self) -> str:
        return f"https://tracker.yandex.ru/{self.key}"

    def name(self) -> str:
        return f"{self.key}: {self.summary}"