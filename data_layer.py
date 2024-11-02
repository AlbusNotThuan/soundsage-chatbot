import chainlit.data as cld

class DataLayer(cld.BaseDataLayer):
    def __init__(self):
        pass

    async def get_user(self, identifier: str) -> Optional["PersistedUser"]:
        pass

    async def create_user(self, user: "User") -> Optional["PersistedUser"]:
        pass

    async def delete_feedback(
        self,
        feedback_id: str,
    ) -> bool:
        pass

    async def upsert_feedback(
        self,
        feedback: Feedback,
    ) -> str:
        pass

    @queue_until_user_message()
    async def create_element(self, element: "Element"):
        pass

    async def get_element(
        self, thread_id: str, element_id: str
    ) -> Optional["ElementDict"]:
        pass

    @queue_until_user_message()
    async def delete_element(self, element_id: str, thread_id: Optional[str] = None):
        pass

    @queue_until_user_message()
    async def create_step(self, step_dict: "StepDict"):
        pass

    @queue_until_user_message()
    async def update_step(self, step_dict: "StepDict"):
        pass

    @queue_until_user_message()
    async def delete_step(self, step_id: str):
        pass