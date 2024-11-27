class TaskDTO:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.key = kwargs.get("key")
        self.summary = kwargs.get("summary")
        self.assignee = kwargs.get("assignee")
        self.status = kwargs.get("status")
        self.due_date = kwargs.get("dueDate")
        self.off_the_plan = kwargs.get("offThePlan")
        self.moving_on_to_the_next_sprint = kwargs.get("movingOnToTheNextSprint")
        self.sp_development = kwargs.get("spDevelopment")
        self.sprint = kwargs.get("sprint")
        self.priority = kwargs.get("priority")
        self.updated_by = kwargs.get("updatedBy")
        self.updated_at = kwargs.get("updatedAt")

    def url(self) -> str:
        return f"https://tracker.yandex.ru/{self.key}"

    def name(self) -> str:
        return f"{self.key}: {self.summary}"
