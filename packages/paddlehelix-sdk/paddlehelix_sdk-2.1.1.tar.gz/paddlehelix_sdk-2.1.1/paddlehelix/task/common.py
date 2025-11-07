import os
import warnings
import logging

import pandas as pd

from paddlehelix import ApiException
from paddlehelix.api.config import *
from paddlehelix.cli.client import get_client
from paddlehelix.sdk_exceptions import SDKError
from paddlehelix.models.tasks_cancel_request import TasksCancelRequest
from paddlehelix.models.tasks_get_request import TasksGetRequest
from paddlehelix.utils.logger import create_logger
from paddlehelix.utils.paddlehelix_utils import ask_yes_no
from paddlehelix.qps_utils import smart_sleep_for_qps, qps_aware_retry

warnings.filterwarnings("ignore")

@qps_aware_retry(max_retries=QPS_RETRY_MAX_ATTEMPTS, 
                base_delay=QPS_RETRY_BASE_DELAY, 
                max_delay=QPS_RETRY_MAX_DELAY, 
                multiplier=QPS_RETRY_MULTIPLIER)
def query_balance():
    """
    Query the current balance.
    """
    client = get_client()
    balance_client_instance = client.balance_client_instance
    response = balance_client_instance.v1_finance_cash_balance_post(_request_timeout=DEFAULT_TIME_OUT)
    balance = response['cashBalance']
    return balance

@qps_aware_retry(max_retries=QPS_RETRY_MAX_ATTEMPTS, 
                base_delay=QPS_RETRY_BASE_DELAY, 
                max_delay=QPS_RETRY_MAX_DELAY, 
                multiplier=QPS_RETRY_MULTIPLIER)
def batch_task_info(task_ids, client=None):
    """
    Get the status of multiple tasks in batch.

    Args:
        task_ids (list): A list of task IDs to query.

        client (Helixfold3Api, optional): The client instance for the task API.

    Returns:
        TasksGetResponse: The response object for the task information query request
    """
    if client is None:
        client = get_client()
    get_task_info_instance = client.task_client_instance
    tasks_get_request = TasksGetRequest(task_ids=task_ids)
    response = get_task_info_instance.api_batch_task_info_post(tasks_get_request=tasks_get_request, _request_timeout=DEFAULT_TIME_OUT)
    return response

@qps_aware_retry(max_retries=QPS_RETRY_MAX_ATTEMPTS, 
                base_delay=QPS_RETRY_BASE_DELAY, 
                max_delay=QPS_RETRY_MAX_DELAY, 
                multiplier=QPS_RETRY_MULTIPLIER)
def batch_task_cancel(task_ids, client=None, logger=None):
    """
    Cancel multiple tasks in batch with QPS exception retry logic.

    Args:
        task_ids (list): A list of task IDs to cancel.
        client (Helixfold3Api, optional): The client instance for the task API.
        logger (logging.Logger, optional): Logger instance for logging.

    Returns:
        TasksCancelResponse: The response object for the task cancellation request.
        
    Raises:
        ApiException: If API call fails after all retries.
        SDKError: If the response indicates failure.
    """
    if client is None:
        client = get_client()
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    cancel_task_instance = client.task_client_instance
    tasks_cancel_request = TasksCancelRequest(task_ids=task_ids)
    
    response = cancel_task_instance.api_batch_task_cancel_post(
        tasks_cancel_request=tasks_cancel_request, 
        _request_timeout=DEFAULT_TIME_OUT
    )
    if response.code != 0:
        raise SDKError(f"Failed to cancel the task with id {task_ids}! Message: {response.msg}")
    return response

def cancel_w_task_ids(task_ids, quiet=False, logger=None):
    """
    Cancels specific tasks.
    """
    if len(task_ids) > MAX_TASK_COUNT:
        logger.error(f"The number of tasks is too large: {len(task_ids)}. The maximum number of tasks is: {MAX_TASK_COUNT}.")
        return []

    if not task_ids:
        logger.info("No tasks to cancel.")
        return []

    if not quiet:
        if not ask_yes_no(f"Found {len(task_ids)} tasks to cancel, are you sure you want to cancel the tasks?", logger):
            logger.info("Stop cancel tasks. Exit.")
            return []
        
    balance = query_balance()
    logger.info(f"Your balance before canceling tasks: {balance}")
        
    client = get_client()
    all_canceled_task_ids = []
    
    # 分批取消任务
    for i in range(0, len(task_ids), MAX_CANCEL_TASK_COUNT):
        batch_task_ids = task_ids[i:i+MAX_CANCEL_TASK_COUNT]
        logger.info(f"Canceling task with id {batch_task_ids} ...")
        
        try:
            # batch_task_cancel 函数内部已经处理了QPS异常重试逻辑
            response = batch_task_cancel(task_ids=batch_task_ids, client=client, logger=logger)
            success_cancel_task_ids = response.data
            all_canceled_task_ids.extend(success_cancel_task_ids)
            
            # 使用智能QPS休眠替代固定休眠
            last_call_time = smart_sleep_for_qps(QPS, getattr(cancel, '_last_call_time', None))
            cancel._last_call_time = last_call_time
            
        except ApiException as e:
            # 如果batch_task_cancel已经重试失败，记录错误并继续处理下一批次
            logger.warning(f"Skipping batch {batch_task_ids} due to API exception: {e}")
            continue
        except SDKError as e:
            # SDKError表示业务逻辑错误，直接抛出
            logger.error(f"SDK error when canceling batch {batch_task_ids}: {e}")
            logger.info(f"Successfully canceled {len(all_canceled_task_ids)}/{len(task_ids)} tasks!")
            raise e

    logger.info(f"Successfully canceled {len(all_canceled_task_ids)}/{len(task_ids)} tasks!")
    balance = query_balance()
    logger.info(f"Your balance after canceling tasks: {balance}")
    return all_canceled_task_ids

def cancel_w_output_dir(output_dir, quiet=False, logger=None):
    """
    Cancels all tasks in the specified output directory.
    """
    table_path = os.path.join(output_dir, "table.csv")
    df = pd.read_csv(table_path)
    submitted_tasks = df[df['status'] == SUBMITTED]
    if submitted_tasks.empty:
        logger.info("There is no task running!")
        return []
    task_id_list = submitted_tasks['task_id'].tolist()
    canceled_task_ids = cancel_w_task_ids(task_id_list, quiet, logger)

    if canceled_task_ids:
        success_indices = df[df['task_id'].isin(canceled_task_ids)].index
        df.loc[success_indices, 'status'] = CANCELLED
        logger.info(f"Canceled task with id {canceled_task_ids}!")
        df.to_csv(table_path, index=False)
    return canceled_task_ids

def cancel(output_dir=None, task_ids=None, quiet=False):
    """
    Cancels specific tasks or all tasks in the specified output directory.
    **Note: The `cancel` function does not report errors when encountering un-cancelable task ids, only reports the number of successfully canceled tasks at the end of execution.**

    Args:
        output_dir (str, optional, mutually exclusive with task_ids): Specifies the output directory where submitted tasks are located.
            - When this parameter is provided, the function will check the `table.csv` file in the `output_dir` directory and cancel all tasks contained within it.

        task_ids (list, optional, mutually exclusive with output_dir): Specifies the list of task IDs to cancel.
            - This parameter must be of **list type**, where each element is a valid `task_id` (integer).
            - If `task_ids` is provided, the function will **not** check the `output_dir` directory.

        quiet (bool, optional, default: False): Whether to enable silent mode.
            - `True`: The function will execute the cancellation operation directly without outputting prompt messages.
            - `False`: The function will output prompt messages before execution and wait for user confirmation before running.

    Returns:
        int: The number of tasks that were canceled.
    """
    # 参数检查
    # 检查 quiet 参数类型
    if not isinstance(quiet, bool):
        raise SDKError(f"quiet must be a boolean, got {type(quiet).__name__}")

    # 检查 output_dir 和 task_ids 的互斥性
    if output_dir is not None and task_ids is not None:
        raise SDKError("output_dir and task_ids are mutually exclusive parameters. Please provide only one of them.")
    
    # 检查是否至少提供了一个参数
    if output_dir is None and task_ids is None:
        raise SDKError("Either output_dir or task_ids must be provided.")
    
    # 检查 task_ids 的类型和内容
    if task_ids is not None:
        if not isinstance(task_ids, list):
            raise SDKError("task_ids must be a list type.")
        if not task_ids:  # 空列表检查
            raise SDKError("task_ids cannot be an empty list.")
        for i, task_id in enumerate(task_ids):
            if not isinstance(task_id, int):
                raise SDKError(f"task_ids[{i}] must be an integer, got {type(task_id).__name__}")
        logger = create_logger(name='cancel')
        return cancel_w_task_ids(task_ids, quiet, logger)
    if output_dir is not None:
        if not isinstance(output_dir, str):
            raise SDKError("output_dir must be a string.")
        table_path = os.path.join(output_dir, "table.csv")
        if not os.path.isdir(output_dir):
            raise SDKError(f"output_dir {output_dir} is not a valid directory.")
        if not os.path.exists(table_path):
            raise SDKError(f"table.csv not found in output_dir {output_dir}.")
        logger = create_logger(output_dir, 'cancel.txt', name='cancel')
        return cancel_w_output_dir(output_dir, quiet, logger)

if __name__ == "__main__":
    print(query_balance())
