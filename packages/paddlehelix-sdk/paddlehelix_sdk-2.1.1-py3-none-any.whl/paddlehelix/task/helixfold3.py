import ast
import json
import os
import time
import warnings
from time import sleep
from pprint import pformat
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from paddlehelix import ApiException, Helixfold3PriceQueryRequest, Helixfold3TaskBatchSubmitRequest
from paddlehelix.api.config import *
from paddlehelix.cli.client import get_client
from paddlehelix.utils.file_util import download_file, parse_filename_from_url
from paddlehelix.utils.logger import create_logger
from paddlehelix.utils.paddlehelix_utils import ask_yes_no, check_existing_submission, init_input
from paddlehelix.task.common import batch_task_info, query_balance
from paddlehelix.utils.graceful_shutdown import GracefulShutdown, set_global_shutdown_manager

# QPS异常处理导入
from paddlehelix.qps_exceptions import is_qps_limit_exception
from paddlehelix.qps_utils import smart_sleep_for_qps, qps_aware_retry

warnings.filterwarnings("ignore")


def _log_task_status_summary(df, logger):
    """
    Log task status summary statistics.
    
    Args:
        df (pandas.DataFrame): DataFrame containing task data with 'status' column
        logger: Logger instance for output
    """
    all_status = df['status'].apply(lambda x: TASK_STATUS_TO_STR[x])
    status_counts = all_status.value_counts().to_frame()
    logger.info("Task status summary:\n" + status_counts.to_markdown(tablefmt='grid'))


@qps_aware_retry(max_retries=QPS_RETRY_MAX_ATTEMPTS, 
                base_delay=QPS_RETRY_BASE_DELAY, 
                max_delay=QPS_RETRY_MAX_DELAY, 
                multiplier=QPS_RETRY_MULTIPLIER)
def query_price(output_dir, input_data=None):
    """
    Query the specific tasks or all tasks in the specified output directory.

    Args:
        output_dir (str, required): Specifies the output directory for storing price query results. 
            - This path can be directly used for subsequent `execute` task submission, meaning price query results are reusable.
            - When querying prices, the program will create a `table.csv` file in the `output_dir` directory to store task price information.

        input_data (str, optional): Specifies the input data for price querying, aligned with `execute`, supporting the following formats:
            - A JSON object
            - A list containing multiple JSON objects
            - A path to a JSON file, with file content as task input
            - A path to a directory containing multiple JSON files, with all files in the directory merged as input
            - If **`input_data` is not provided**, the program will default to using the existing table.csv table in the `output_dir` directory for price querying.

    Returns:
        float: The total price of the tasks.
    """
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    logger = create_logger(output_dir, 'query_price.txt', name='query_price')

    table_path = os.path.join(output_dir, "table.csv")

    if input_data is None and not os.path.exists(table_path):
        logger.error(f"No task data to query price!")
        return False
    elif input_data is not None and not os.path.exists(table_path):
        try:
            df = init_input(output_dir, INITIALIZATION, input_data=input_data)
        except ValueError as e:
            logger.error(f"Input Error!")
            logger.error(f"{e}")
            return False
    elif input_data is None and os.path.exists(table_path):
        df = pd.read_csv(table_path)
    elif input_data is not None and os.path.exists(table_path):
        logger.info(f"There is an old submission under folder: {output_dir}, checking status ...")
        success, df = check_existing_submission(output_dir, logger, quiet=True)
        if not success:
            return False
    
    if len(df) > MAX_TASK_COUNT:
        logger.error(f"The number of tasks is too large: {len(df)}. The maximum number of tasks is: {MAX_TASK_COUNT}.")
        return False

    not_submitted_mask = (df['status'] == INITIALIZATION) | (df['status'] == NOT_STARTED)
    initial_mask = df['status'] == INITIALIZATION
    logger.info(f"Query price for unsubmitted tasks, total task number {not_submitted_mask.sum()} ...")

    # Query price, calculated by batch
    client = get_client()
    price_query_client_instance = client.helixfold3_client_instance
    initial_indices = df.index[initial_mask]
    for batch_start in range(0, len(initial_indices), QUERY_PRICE_BATCH_DATA_NUM):
        batch_indices = initial_indices[batch_start:batch_start + QUERY_PRICE_BATCH_DATA_NUM]
        batch_query_price_task_list = df.iloc[batch_indices]['data'].apply(ast.literal_eval).to_list()

        price_query_request = Helixfold3PriceQueryRequest(tasks=batch_query_price_task_list)
        try:
            response = price_query_client_instance.api_batch_submit_helixfold3_price_post(helixfold3_price_query_request=price_query_request, _request_timeout=DEFAULT_TIME_OUT)
        except ApiException as e:
            if is_qps_limit_exception(e):
                raise e
            logger.error(f"ApiException when calling Helixfold3Api->batch_submit_helixfold3_price_post for the #{batch_indices[0]+1}-#{batch_indices[-1]+1} task!")
            logger.error(f"Please check your network connection and try submitting again under the same folder: {output_dir}")
            return False
        if response.code != 0:
            logger.error(f"Failed to query price for the #{batch_indices[0]+1}-#{batch_indices[-1]+1} task! Message: {response.msg}")
            logger.error(f"If no problems found, please re-submit tasks from the same folder: {output_dir}")
            return False

        prices = [price.price for price in response.data.prices]
        # 使用智能QPS休眠替代固定休眠
        last_call_time = smart_sleep_for_qps(QPS, getattr(query_price, '_last_call_time', None))
        query_price._last_call_time = last_call_time
        for i, i_table in enumerate(batch_indices):
            if df.loc[i_table, 'status'] == INITIALIZATION:
                df.loc[i_table, 'status'] = NOT_STARTED
                df.loc[i_table, 'price'] = prices[i]

    total_prices = df[not_submitted_mask]['price'].sum()
    df.to_csv(table_path, index=False)
    df['status'] = df['status'].apply(lambda x: TASK_STATUS_TO_STR[x])
    df['data'] = df['data'].apply(lambda x: x[:100] + '...' if len(x) > 100 else x)
    logger.info('Price of tasks:\n' + df[['data', 'price', 'status']].to_markdown(index=False, tablefmt='grid'))
    logger.info(f"Total price for unsubmitted tasks: {total_prices:.2f}")
    return total_prices

@qps_aware_retry(max_retries=QPS_RETRY_MAX_ATTEMPTS, 
                base_delay=QPS_RETRY_BASE_DELAY, 
                max_delay=QPS_RETRY_MAX_DELAY, 
                multiplier=QPS_RETRY_MULTIPLIER)
def submit(output_dir, input_data=None, quiet=False):
    """
    Submits specific tasks or all tasks in the specified output directory.

    Args:
        output_dir (str): The output directory where tasks are stored.
            - This directory contains task statuses, logs, and other related data.
            - If the `output_dir` exists, the program prioritizes submitting tasks in this directory rather than using the `input_data` parameter.

        input_data (str, optional): Specifies the input data for the task.
            - The input data can be:
                - A JSON file
                - A folder containing multiple JSON files
                - A JSON object
                - A list of JSON objects

        quiet (bool, optional): Whether to enable silent mode. Defaults to `False`.
            - `True`: Executes the submission without displaying prompt messages.
            - `False`: Displays a prompt message before executing the submission and waits for user confirmation.

    Returns:
        bool: `True` if the task submission is successful, otherwise `False`.
    """
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    logger = create_logger(output_dir, 'submit.txt', name='submit')
    
    # 使用优雅退出管理器保护整个提交过程
    with GracefulShutdown(timeout=60, logger=logger) as shutdown_manager:
        set_global_shutdown_manager(shutdown_manager)
        
        table_path = os.path.join(output_dir, "table.csv")

        if input_data is None and not os.path.exists(table_path):
            logger.error(f"No task data to submit!")
            return False
        elif input_data is not None and not os.path.exists(table_path):
            try:
                df = init_input(output_dir, NOT_STARTED, input_data=input_data)
            except ValueError as e:
                logger.error(f"Input Error!")
                logger.error(f"{e}")
                return False
        elif input_data is None and os.path.exists(table_path):
            df = pd.read_csv(table_path)
        elif input_data is not None and os.path.exists(table_path):
            logger.info(f"There is an old submission under folder: {output_dir}, checking status ...")
            success, df = check_existing_submission(output_dir, logger, quiet=quiet)
            if not success:
                return False

        ready_submit_mask = df['status'] == NOT_STARTED
        if not quiet:
            if not ask_yes_no(f"Ready to submit {len(df[ready_submit_mask])} tasks!", logger):
                logger.info(f"Exit.")
                return False

        client = get_client()
        # Process in batches
        batch_submit_instance = client.helixfold3_client_instance
        for batch_start in range(0, len(df[ready_submit_mask]), DEFAULT_TASK_COUNT_ONE_BATCH):
            # 检查是否收到退出信号
            if shutdown_manager.is_shutdown_requested():
                logger.warning("Received shutdown signal, exiting batch submission ...")
                return False
                
            batch_indices = df[ready_submit_mask].index[batch_start:batch_start + DEFAULT_TASK_COUNT_ONE_BATCH]
            ready_submit_task_list = df.iloc[batch_indices]['data'].apply(ast.literal_eval).to_list()

            batch_submit_request = Helixfold3TaskBatchSubmitRequest(tasks=ready_submit_task_list)
            
            # 保护API调用操作
            with shutdown_manager.protect_operation(f"Submit batch #{batch_indices[0]+1}-#{batch_indices[-1]+1}"):
                try:
                    response = batch_submit_instance.api_batch_submit_helixfold3_post(helixfold3_task_batch_submit_request=batch_submit_request, _request_timeout=DEFAULT_TIME_OUT)
                except ApiException as e:
                    if is_qps_limit_exception(e):
                        raise e
                    # 其他异常，按原有逻辑处理
                    logger.error(f"ApiException when calling Helixfold3Api->batch_submit_helixfold3_post for the #{batch_indices[0]+1}-#{batch_indices[-1]+1} task!")
                    logger.error(f"Please check your network connection and try submitting again under the same folder: {output_dir}")
                    return False
                if response.code != 0:
                    logger.error(f"Failed to submit task from #{batch_indices[0]+1} to #{batch_indices[-1]+1}!  Message: {response.msg}")
                    logger.error(f"If no problem found, please re-submit tasks from the same folder: {output_dir}")
                    return False

                task_ids = response.data.task_ids
                logger.info(f"Batch submit task: {task_ids}")
                # Update task_list and dataframe
                df.loc[batch_indices, 'task_id'] = task_ids
                df.loc[batch_indices, 'status'] = SUBMITTED

                # 使用智能QPS休眠替代固定休眠
                last_call_time = smart_sleep_for_qps(QPS, getattr(submit, '_last_call_time', None))
                submit._last_call_time = last_call_time

                # Save updated dataframe
                df.to_csv(table_path, index=False)
        
        logger.info(f"All tasks submitted!")
        df['status'] = df['status'].apply(lambda x: TASK_STATUS_TO_STR[x])
        df['data'] = df['data'].apply(lambda x: x[:100] + '...' if len(x) > 100 else x)
        logger.info("Submitted tasks:\n" + df[['task_id', 'status', 'data']].to_markdown(index=False, tablefmt='grid'))
        return True

@qps_aware_retry(max_retries=QPS_RETRY_MAX_ATTEMPTS, 
                base_delay=QPS_RETRY_BASE_DELAY, 
                max_delay=QPS_RETRY_MAX_DELAY, 
                multiplier=QPS_RETRY_MULTIPLIER)
def polling_task_status(output_dir):
    logger = create_logger(output_dir, 'polling_task.txt', name='polling_task')
    logger.info("Starting task status polling!")
    table_path = os.path.join(output_dir, "table.csv")
    save_dir = os.path.join(os.path.dirname(table_path), "result")
    df = pd.read_csv(table_path, dtype={'download_url': str})

    download_futures = []
    exe = ThreadPoolExecutor(max_workers=CONCURRENT_DOWNLOAD_NUM)

    def _check_download_futures():
        for fut in download_futures:
            if fut.done():
                download_futures.remove(fut)
                idx = fut.result()
                df.loc[idx, 'status'] = DOWNLOADED
                df.loc[idx, 'storage_path'] = os.path.join(save_dir, parse_filename_from_url(df.loc[idx, 'download_url']))
                logger.info(f"Task #{idx} downloaded.")
                if fut.exception() is not None:
                    logger.error(f"Task #{idx} download failed! Please restart the submission to retry!")
                    raise fut.exception()

    # 如果表中有未下载的任务，优先启动他们的下载
    to_down = df['status'] == QUERIED
    for idx, row in df[to_down].iterrows():
        download_futures.append(exe.submit(download_file, idx, df.loc[idx, 'download_url'], save_dir))

    # 开始轮询，发现已完成的任务则启动下载
    client = get_client()
    summary_print_interval = 30
    summary_print_last_time = time.time()
    _log_task_status_summary(df, logger)
    while True:
        # Get tasks that need to query status
        query_mask = df['status'] == SUBMITTED
        tasks_to_query = df[query_mask]

        for i in range(0, len(tasks_to_query), QUERY_BATCH_NUM):
            batch_indices = tasks_to_query.index[i:i+QUERY_BATCH_NUM]
            batch_task_ids = tasks_to_query.loc[batch_indices, 'task_id'].tolist()
            try:
                response = batch_task_info(batch_task_ids, client)
            except ApiException as e:
                if is_qps_limit_exception(e):
                    raise e
                logger.error(f"ApiException when calling TaskApi->batch_task_info for the task with ids {batch_task_ids}! Message: {e}")
                logger.error(f"Please check your network connection and try submitting again under the same folder: {output_dir}")
                return False
            if response.code != 0:
                logger.error(f"Failed to get task info for the task with ids {batch_task_ids}! Message: {response.msg}")
                logger.error(f"If no problem found, please re-submit tasks from the same folder: {output_dir}")
                return False

            assert len(batch_indices) == len(response.data), f"You are trying to query status of non-existing tasks! Please check the input task ids: {batch_task_ids}"

            for idx, task_info in zip(batch_indices, response.data):
                status = task_info.status
                if status == ApiTaskStatusSucc:
                    df.loc[idx, 'status'] = QUERIED
                    df.loc[idx, 'download_url'] = json.loads(task_info.result)['download_url']
                    download_futures.append(exe.submit(download_file, idx, df.loc[idx, 'download_url'], save_dir))
                elif status == ApiTaskStatusFailed:
                    df.loc[idx, 'status'] = FAILED
                elif status == ApiTaskStatusCancel:
                    df.loc[idx, 'status'] = CANCELLED

                while len(download_futures) >= 10:
                    try:
                        _check_download_futures()
                    except Exception as e:
                        logger.error(f"Exception when downloading task results! Please check your network connection and try again.")
                        return False
                    sleep(5)

            df.to_csv(table_path, index=False)
            if time.time() - summary_print_last_time >= summary_print_interval:
                summary_print_last_time = time.time()
                _log_task_status_summary(df, logger)
            
            # 使用智能QPS休眠替代固定休眠
            last_call_time = smart_sleep_for_qps(QPS, getattr(polling_task_status, '_last_call_time', None))
            polling_task_status._last_call_time = last_call_time

        while download_futures:
            try:
                _check_download_futures()
            except Exception as e:
                logger.error(f"Exception when downloading task results! Please check your network connection and try again.")
                return False
            sleep(5)
        df.to_csv(table_path, index=False)
        if not (df['status'] == SUBMITTED).any():
            return True


def execute(output_dir,
            input_data=None,
            quiet=False,
            ignore_balance=False,
            **kwargs):
    """
    Executes the task submission process.

    Args:
        output_dir (str): Specifies the directory for storing logs and results.
            - If this path was previously used for a submitted task, the system will automatically read the status files from the directory and resume execution from where the last task left off.
            - If you want to start a new task from scratch, provide a new, unused directory.

        input_data (str): Specifies the input data path for the task.
            - The input data can be:
                - A JSON file
                - A folder containing multiple JSON files
                - A JSON object
                - A list of JSON objects

        quiet (bool): Determines whether to skip the confirmation prompt before submitting the task.
            - If set to `True`, the system will automatically submit the task without asking for confirmation.
            - If set to `False`, the system will prompt the user for confirmation before submission.

        ignore_balance (bool): **(Internal use only)** A developer-only flag. Do not use this parameter.
    Returns:
        bool: `True` if the task submission is successful, otherwise `False`.
    """

    # 1. 结果路径初始化，读取或初始化任务表格
    table_path = os.path.join(output_dir, "table.csv")
    if not os.path.isdir(output_dir) or not os.path.exists(table_path):
        os.makedirs(output_dir, exist_ok=True)
        logger = create_logger(output_dir, 'main.txt', name='main')
        logger.info("Creating a new folder {} to store task data and results.".format(output_dir))
        try:
            df = init_input(output_dir, INITIALIZATION, input_data, **kwargs)
        except ValueError as e:
            logger.error(f"Input Error!")
            logger.error(f"{e}")
            return False
    else:
        logger = create_logger(output_dir, 'main.txt', name='main')
        logger.info(f"There is an old submission under folder: {output_dir}, checking status ...")
        success, df = check_existing_submission(output_dir, logger, quiet=False)
        if not success:
            return False

    if len(df) > MAX_TASK_COUNT:
        logger.error(f"The number of tasks is too large: {len(df)}. The maximum number of tasks is: {MAX_TASK_COUNT}.")
        return False

    # 2. 询价
    if ((df['status'] == INITIALIZATION) | (df['status'] == NOT_STARTED)).any():
        total_prices = query_price(output_dir)
        if not total_prices:
            return False

    # 3 提交任务
    df = pd.read_csv(table_path)
    if (df['status'] == NOT_STARTED).any():
        # 3.1 询问余额，与待提交任务的价格比较
        if not ignore_balance:
            try:
                balance = query_balance()
            except Exception as e:
                logger.error("ApiException when calling BceApi->v1_finance_cash_balance: %s\n" % e)
                return False
            logger.info(f"Current balance: {balance}")
            total_prices = df[df['status'] == NOT_STARTED]['price'].sum()
            if total_prices > balance:
                logger.info("Insufficient balance! Exit! Please go to https://console.bce.baidu.com/finance/recharge to recharge and submit the task again.")
                return False
            else:
                if not quiet and not ask_yes_no(f"Sufficient balance! Please confirm to start the submission:", logger):
                    logger.info(f"Exit.")
                    return False
        else:
            logger.warning("Debug mode! Skip balance checking. Continue ...")

        # 3.2
        df = pd.read_csv(table_path)
        if not submit(output_dir, quiet=quiet):
            return False

    # 4. 轮询任务运行状态
    df = pd.read_csv(table_path)
    if (df['status'] == SUBMITTED).any():
        if not polling_task_status(output_dir):
            return False

    logger.info("All tasks finished!")

    df = pd.read_csv(table_path)
    _log_task_status_summary(df, logger)

    df['status'] = df['status'].apply(lambda x: TASK_STATUS_TO_STR[x])
    logger.info('Task summary:\n'+ df[['task_id', 'status', 'price', 'storage_path']].to_markdown(index=False, tablefmt='grid'))
    logger.info("The submission summary printed above are stored in: {}".format(table_path))
    return True
