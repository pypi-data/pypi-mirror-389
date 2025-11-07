"""
PaddleHelix API Collection
"""


class APIConfig:
    def __init__(self, name: str, uri):
        self.name = name
        self.uri = uri


class ServerAPIRegistry:
    class HelixFold3:
        name = "HelixFold3"
        submit = APIConfig("submit", "/api/submit/helixfold3")
        batch_submit = APIConfig("batch_submit", "/api/batch/submit/helixfold3")
        query_task_price = APIConfig("query_task_price", "/api/batch/submit/helixfold3/price")

    class Common:
        query_task_info = APIConfig("query_task_info", "/api/task/info")
        cancel_task = APIConfig("cancel_task", "/api/task/cancel")


class ClientAPIRepository:
    download_result = APIConfig("download_result", "")
