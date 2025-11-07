"""
Task structure
"""
import os.path
import warnings
from typing import Any

from paddlehelix.api.config import MAX_TASK_COUNT
from paddlehelix.utils import file_util
from paddlehelix.version.structures import dict_type, list_type

class TaskUtil:
    @staticmethod
    def parse_task_data_list_from_file(file_path: str):
        pending_data_list = []
        content_type = file_util.check_json_type(file_path)
        if content_type == 'dict':
            data = file_util.parse_json_from_file(file_path)
            pending_data_list.append(data)
        elif content_type == 'list':
            data_list = file_util.parse_json_list_from_file(file_path)
            for idx, data in enumerate(data_list):
                pending_data_list.append(data)
        else:
            raise "The content format of the file indicated by the parameter file_path is invalid."
        return pending_data_list

    @staticmethod
    def validate_input(task_list):
        if len(task_list) > MAX_TASK_COUNT:
            raise ValueError(f"The number of tasks is too large: {len(task_list)}. The maximum number of tasks is: {MAX_TASK_COUNT}.")
        if len(task_list) == 0:
            raise ValueError(f"The number of tasks is 0.")
        for i, task in enumerate(task_list):
            if not isinstance(task, dict_type):
                raise ValueError(f"The task data is not of dict type: {task}")
            if 'model_type' in task and task['model_type'] not in ['HelixFold3', 'HelixFold-S1']:
                raise ValueError(f"The model type is not supported: {task['model_type']}. Supported model types are: HelixFold3, HelixFold-S1.")
            if 'entities' not in task:
                raise ValueError(f"'entities' is missing in the #{i} task: {task}")
            entities = task['entities']
            for entity in entities:
                if not isinstance(entity, dict_type):
                    raise ValueError(f"The entity data is not of dict type: {entity}. The task data is: {task}")
                if 'type' not in entity:
                    raise ValueError(f"The entity data is missing the 'type' field: {entity}. The task data is: {task}")
                if entity['type'] not in ['protein', 'dna', 'rna', 'ligand', 'ion']:
                    raise ValueError(f"The entity type is not supported: {entity['type']}. The task data is: {task}")


    @staticmethod
    def parse_task_data_list_from_all_kinds_input(input_data = None,
                                                  data: dict_type[str, Any] = None,
                                                  data_list: list_type[dict_type[str, Any]] = None,
                                                  **kwargs) -> list_type[dict_type[str, Any]]:
        pending_data_list = []

        if input_data is not None:
            if isinstance(input_data, dict_type):
                pending_data_list.append(input_data)
            elif isinstance(input_data, list_type):
                for idx, data in enumerate(input_data):
                    pending_data_list.append(data)
            else:
                if os.path.isfile(input_data):
                    data_list = TaskUtil.parse_task_data_list_from_file(input_data)
                    pending_data_list += data_list
                elif os.path.isdir(input_data):
                    file_paths = file_util.get_all_file_paths(input_data)
                    for file_path in file_paths:
                        data_list = TaskUtil.parse_task_data_list_from_file(file_path)
                        pending_data_list += data_list
                else:
                    raise ValueError(f"The content format of the file indicated by the parameter input_data is invalid.")
        else:
            if data is not None:
                warnings.warn(
                    "The parameter 'data' will be deprecated in the future. Please use 'input_data' instead.",
                    category=DeprecationWarning,
                    stacklevel=2
                )
                assert isinstance(data, dict_type), "The parameter data is not of dict type."
                pending_data_list.append(data)
            # process the task data in 'data_list'
            if data_list is not None:
                warnings.warn(
                    "The parameter 'data_list' will be deprecated in the future. Please use 'input_data' instead.",
                    category=DeprecationWarning,
                    stacklevel=2
                )
                assert isinstance(data_list, list_type), "The parameter data_list is not of list type."
                for idx, data in enumerate(data_list):
                    pending_data_list.append(data)
            # process the task data in 'file_path'
            if "file_path" in kwargs:
                warnings.warn(
                    "The parameter 'file_path' will be deprecated in the future. Please use 'input_data' instead.",
                    category=DeprecationWarning,
                    stacklevel=2
                )
                file_path = kwargs.get("file_path")
                assert isinstance(file_path, str), "The parameter file_path is not of str type."
                if not os.path.isfile(file_path):
                    raise "The parameter file_path cannot represent a valid file."
                data_list = TaskUtil.parse_task_data_list_from_file(file_path)
                pending_data_list += data_list
            # process the task data in 'file_dir'
            if "file_dir" in kwargs:
                warnings.warn(
                    "The parameter 'file_dir' will be deprecated in the future. Please use 'input_data' instead.",
                    category=DeprecationWarning,
                    stacklevel=2
                )
                file_dir = kwargs.get("file_dir")
                assert isinstance(file_dir, str), "The parameter file_dir is not of str type."
                if not os.path.isdir(file_dir):
                    raise "The parameter file_dir cannot represent a valid file dir."
                file_paths = file_util.get_all_file_paths(file_dir)
                for file_path in file_paths:
                    data_list = TaskUtil.parse_task_data_list_from_file(file_path)
                    pending_data_list += data_list

        TaskUtil.validate_input(pending_data_list)

        return pending_data_list