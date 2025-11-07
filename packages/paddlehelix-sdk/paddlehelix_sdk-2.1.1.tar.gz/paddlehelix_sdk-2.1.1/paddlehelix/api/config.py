"""
Common request variables.
"""

# 请求变量
SCHEME = "http://"
HOST = "chpc.bj.baidubce.com"
BALANCE_HOST = 'billing.baidubce.com'

# API 返回状态
ApiTaskStatusCancel = -2  # 取消
ApiTaskStatusFailed = -1  # 执行失败
ApiTaskStatusUnknown = 0  # 未知状态
ApiTaskStatusSucc = 1  # 成功
ApiTaskStatusDoing = 2  # 运行中

# 单个任务在 SDK 流程中的状态
INITIALIZATION = -3
NOT_STARTED = 0
SUBMITTED = 1
QUERIED = 2
DOWNLOADED = 3
FAILED = -1
CANCELLED = -2

TASK_STATUS_TO_STR = {
    INITIALIZATION: "INITIALIZATION",
    NOT_STARTED: "NOT_STARTED",
    SUBMITTED: "SUBMITTED",
    QUERIED: "DONE",
    DOWNLOADED: "DOWNLOADED",
    FAILED: "FAILED",
    CANCELLED: "CANCELLED"
}

# 超时重试参数
DEFAULT_RETRY_COUNT = 3
DEFAULT_TIME_OUT = 10

# QPS限流参数，目前所有接口均改为批量，QPS无需太高
QPS = 0.5

# QPS重试参数
QPS_RETRY_MAX_ATTEMPTS = 5      # 最大重试次数
QPS_RETRY_BASE_DELAY = 1        # 基础重试延迟（秒）
QPS_RETRY_MAX_DELAY = 60        # 最大重试延迟（秒）
QPS_RETRY_MULTIPLIER = 2        # 重试延迟倍数
QPS_ENABLE_SMART_RETRY = True   # 是否启用智能重试

# 提交任务参数
DEFAULT_TASK_COUNT_ONE_BATCH = 20

# 轮询任务参数
QUERY_BATCH_NUM = 50
CONCURRENT_DOWNLOAD_NUM = 4

# 询价单批次数量
QUERY_PRICE_BATCH_DATA_NUM = 100

# 单次取消任务数量
MAX_CANCEL_TASK_COUNT = 100

MAX_TASK_COUNT = 1000