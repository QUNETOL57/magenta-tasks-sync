import logging

import yaml

logger = logging.getLogger(__name__)


class TaskDTO:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.key = kwargs.get("key")
        self._summary = kwargs.get("summary", "")  # Значение по умолчанию
        self.stage_deadline = kwargs.get("stageDeadline")
        self.type = kwargs.get("type")
        self._assignee = kwargs.get("assignee")
        self.status = kwargs.get("status")
        self.due_date = kwargs.get("dueDate")
        self._off_the_plan = kwargs.get("offThePlan")
        self._moving_on_to_the_next_sprint = kwargs.get("movingOnToTheNextSprint")
        self.sp_development = kwargs.get("spDevelopment")
        self.sprint = kwargs.get("sprint")
        self.priority = kwargs.get("priority")
        self.updated_by = kwargs.get("updatedBy")
        self.updated_at = kwargs.get("updatedAt")
        self._outside_of_the_sprint_plan = kwargs.get("outsideOfTheSprintPlan")
        self.project = kwargs.get("project")
        self.deadline_fact = kwargs.get("deadlineFact")
        self.sp_testing = kwargs.get("spTesting")
        self._dev = kwargs.get("dev")
        self._qa_engineer = kwargs.get("qaEngineer")
        self._analyst = kwargs.get("analyst")

        self._load_mapping_assignee()

    def _load_mapping_assignee(self):
        """Загружает маппинги из YAML файла"""
        try:
            with open('mapping.yaml', 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                self.mapping_assignee = data.get('assignee', {})
        except FileNotFoundError:
            logger.error("Mapping file not found, using empty mapping")
            self.mapping_assignee = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing mapping file: {e}")
            raise

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

    @property
    def outside_sprint(self):
        return bool(self._outside_of_the_sprint_plan)

    @property
    def assignee(self):
        return self.mapping_assignee.get(self._assignee, self._assignee)

    @property
    def dev(self):
        return self.mapping_assignee.get(self._dev, self._dev)

    @property
    def qa_engineer(self):
        return self.mapping_assignee.get(self._qa_engineer, self._qa_engineer)

    @property
    def analyst(self):
        return self.mapping_assignee.get(self._analyst, self._analyst)

    def url(self) -> str:
        return f"https://tracker.yandex.ru/{self.key}"

    def name(self) -> str:
        return f"{self.key}: {self.summary}"
