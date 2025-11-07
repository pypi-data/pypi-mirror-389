"""
File operation utility methods.
"""
import hashlib
import json
import shutil
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
import requests

from paddlehelix.version.structures import dict_type, list_type

import os


def download_file(idx: int, url: str, save_dir: str) -> str:
    """
    Download a file.

    Args:
        idx (int): Index of task in the table.
        save_dir (str): Directory to save the file.
        url (str): Download URL.

    Returns:
        str: File save path, which is download_dir + '/' + filename.
    """
    filename = parse_filename_from_url(url)
    create_directories(save_dir)
    
    # 发起 GET 请求，stream=True 表示流式下载
    response = requests.get(url, stream=True)
    response.raise_for_status()  # 检查请求是否成功

    # 打开目标文件进行写入
    path = os.path.join(save_dir, filename)
    with open(path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):  # 按块读取内容
            if chunk:  # 确保块不为空
                file.write(chunk)  # 写入文件
    return idx


def parse_filename_from_url(url: str) -> str:
    """
    Parse the filename from a given URL.

    Args:
        url (str): The URL from which to extract the filename.

    Returns:
        str: The extracted filename.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    return filename


def clear_dir(target_dir: str) -> bool:
    """
    Clear the directory; if the directory exists, clear all files/folders within it; if the directory does not exist, create the directory.

    Args:
        target_dir (str): Path to the target directory.

    Returns:
        bool: True indicates that the operation was successful; False indicates an operation error.
    """
    try:
        if os.path.exists(target_dir):
            for filename in os.listdir(target_dir):
                file_path = os.path.join(target_dir, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        else:
            os.makedirs(target_dir)
        return True
    except Exception as e:
        print(f"clear folder error: {e}")
        return False


def parse_json_from_file(file_path: str) -> dict_type[str, Any]:
    """
    Read the file and parse the contents into a JSON object.

    Args:
        file_path (str): JSON file path.

    Returns:
        dict: Parsed JSON.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        if isinstance(data, dict_type):
            return data
        else:
            return {}
    except FileNotFoundError:
        print(f"file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"file content is not valid json: {file_path}")
        return {}
    except Exception as e:
        print(f"occur error: {str(e)}")
        return {}


def parse_json_list_from_file(file_path: str) -> list_type[dict_type[str, Any]]:
    """
    Read the file and parse the contents into a list, where each element is a JSON object.

    Args:
        file_path (str): JSON file path.

    Returns:
        list: Parsed JSON list.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if isinstance(data, list_type):
            return data
        else:
            print(f"file content is not valid json list: {file_path}")
            return []
    except FileNotFoundError:
        print(f"file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"file content is not valid json: {file_path}")
        return []
    except Exception as e:
        print(f"occur error: {str(e)}")
        return []


def check_json_type(file_path: str) -> str:
    """
    Judge JSON file contents is list or dict.

    Args:
        file_path (str): JSON file path.

    Returns:
        str: Returns 'list' if list, returns 'dict' if dict, otherwise 'invalid'.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if isinstance(data, list_type):
                return 'list'
            elif isinstance(data, dict_type):
                return 'dict'
            else:
                return 'invalid'
    except json.JSONDecodeError:
        return 'invalid'
    except Exception as e:
        print(f"read file occur error: {e}")
        return 'invalid'


def create_directories(dir_path: str):
    """
    Create multiple folders if they do not exist.

    Args:
        dir_path (str): The path to the directory to create.

    Returns:
        None
    """
    try:
        if os.path.exists(dir_path):
            return
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"create folder occur error: {e}")


def generate_directory_name() -> str:
    """
    Generate a folder name in the format 'batch-download-timestamp'.

    Returns:
        str: The generated folder name.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    directory_name = f"batch-download-{timestamp}"
    return directory_name


def is_exist_result_for_task_data(result_dir: str) -> bool:
    """
    Check if there is a result for the task data in the specified directory.

    Args:
        result_dir (str): The directory to check for task data results.

    Returns:
        bool: True if there is a result for the task data, False otherwise.
    """
    if not os.path.isdir(result_dir):
        return False
    if is_empty_dir(result_dir):
        return False
    file = os.listdir(result_dir)[0]
    return not is_empty_dir(os.path.join(result_dir, file))


def delete_dir_if_exist(file_dir: str):
    """
    Delete the specified directory if it exists.

    Args:
        file_dir (str): The directory to delete.

    Returns:
        None
    """
    if not os.path.isdir(file_dir):
        return
    shutil.rmtree(file_dir)


def get_first_filename(file_dir: str) -> str:
    """
    Get the first filename in the specified directory.

    Args:
        file_dir (str): The directory to get the first filename from.

    Returns:
        str: The first filename in the directory.
    """
    return os.listdir(file_dir)[0]


def get_all_file_paths(file_dir: str) -> list_type[str]:
    """
    Get all file paths in the specified directory.

    Args:
        file_dir (str): The directory to get all file paths from.

    Returns:
        list: A list of all file paths in the directory.
    """
    file_paths = []
    directory = os.path.abspath(file_dir)
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_paths.append(file_path)
    return file_paths


def is_empty_dir(file_dir):
    """
    Check if a directory is empty.

    Args:
        file_dir (str): The directory to check.

    Returns:
        bool: True if the directory is empty, False otherwise.
    """
    if not os.path.isdir(file_dir):
        return False
    files = os.listdir(file_dir)
    return len(files) == 0


def dict_to_unique_filename(data: dict_type) -> str:
    """
    Generate a unique filename from a dictionary by hashing its JSON representation.

    Args:
        data (dict): The dictionary to hash.

    Returns:
        str: A unique filename generated from the dictionary.
    """
    json_str = json.dumps(data, sort_keys=True)
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))
    unique_str = hash_obj.hexdigest()[:16]
    return unique_str


def create_file_if_not_exists(file_path: str) -> bool:
    """
    Creates an empty file at the specified path if the file does not exist.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file was created, False if the file already existed.
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        # Create the empty file
        try:
            with open(file_path, 'w') as file:
                # The file is opened in write mode, which will create it if it doesn't exist
                # No need to write anything to it since we just want an empty file
                pass
                # If the file was created successfully, return True
            return True
        except Exception as e:
            # In case an error occurs while trying to create the file
            # (this should rarely happen for simple file creation)
            print(f"An error occurred while trying to create the file: {e}")
            return False
    else:
        # If the file already exists, return False
        return False


def clean_file(file_path: str) -> bool:
    """
    Clean the file.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file was cleaned successfully, False otherwise.
    """
    try:
        with open(file_path, 'w') as _:
            pass
        return True
    except Exception as e:
        print(f"Error clean the file: {e}")
        return False


def write_dict_to_file(file_path: str, data: dict) -> None:
    """
    Writes a dictionary to a file in JSON format, overwriting any existing content.

    Args:
        file_path (str): The path to the file where the dictionary will be written.
        data (dict): The dictionary to be written to the file.

    Returns:
        None
    """
    # Open the file in write mode ('w') to overwrite any existing content.
    with open(file_path, 'w', encoding='utf-8') as file:
        # Use json.dump to serialize the dictionary as a JSON string and write it to the file.
        # The ensure_ascii=False parameter ensures that non-ASCII characters are written correctly.
        # The indent=4 parameter is optional and used to make the JSON output more readable by adding indentation.
        json.dump(data, file, ensure_ascii=False, indent=4)


def is_file_empty(file_path: str) -> bool:
    """
    Check if a file is empty by examining its size.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file is empty, False otherwise.
    """
    # Get the size of the file in bytes
    file_size = os.path.getsize(file_path)
    # Return True if the size is 0, otherwise False
    return file_size == 0
