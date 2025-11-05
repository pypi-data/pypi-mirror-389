import json
from typing import Optional, Any, List
from pathlib import Path as FSPath
from .nodepath import NodePath
from .result import NoDataError


class NodePathTracker:
    def __init__(self):
        self.path_tracker = []

    def track(self, path: NodePath):
        self.path_tracker.append(str(path))

    def get_paths(self) -> List[NodePath]:
        return self.path_tracker


class Node:
    # Root path constant to avoid repeated NodePath.parse(".") calls
    _ROOT_PATH = NodePath.parse('.')

    def __init__(self, path: NodePath, data: dict, path_tracker: NodePathTracker):
        if not data:
            raise ValueError('data dictionary cannot be empty')
        if 'merged_blob' not in data:
            raise ValueError("data must contain 'merged_blob' key")
        if 'metadata_instances' not in data:
            raise ValueError("data must contain 'metadata_instances' key")
        if 'bundle_info' not in data:
            raise ValueError("data must contain 'bundle_info' key")

        if not path_tracker:
            raise ValueError('path_tracker cannot be None')

        self._path = path
        self._data = data
        self._path_tracker = path_tracker

    @classmethod
    def from_file(
        cls,
        file_path: FSPath,
    ) -> 'Node':
        if not file_path.is_absolute():
            raise ValueError('path must be an absolute path')

        with file_path.open() as f:
            data = json.load(f)

        return cls(cls._ROOT_PATH, data, NodePathTracker())

    @classmethod
    def from_bundle_json(
        cls,
        json_str: str,
    ) -> 'Node':
        data = json.loads(json_str)
        return cls(cls._ROOT_PATH, data, NodePathTracker())

    @classmethod
    def from_merged_json(
        cls,
        json_str: str,
        bundle_info: Optional[dict] = None,
    ) -> 'Node':
        if bundle_info is None:
            bundle_info = {}

        merged_json = json.loads(json_str)
        return cls(
            cls._ROOT_PATH,
            {
                'bundle_info': bundle_info,
                'merged_blob': merged_json,
                'metadata_instances': [{'payload': merged_json}],
            },
            NodePathTracker(),
        )

    def _workflows_finished(self) -> bool:
        bundle_info = self._data.get('bundle_info', {})
        if not bundle_info:
            return False

        return bundle_info.get('workflows_finished', False)

    def get_node(self, path: str) -> 'Node':
        new_path = self._path.concat(path)
        return self.__class__(new_path, self._data, self._path_tracker)

    def exists(self, path: str = '.') -> bool:
        full_path = self._path.concat(path)
        self._path_tracker.track(full_path)

        return full_path.get_value(self._data['merged_blob']) is not None

    def get_value(self, path: str = '.') -> Any:
        full_path = self._path.concat(path)
        self._path_tracker.track(full_path)

        result = full_path.get_value(self._data['merged_blob'])

        if result is None:
            if self._workflows_finished():
                raise ValueError(f'No data found at path {path}')
            else:
                raise NoDataError(f'No data found at path {path}')

        return result

    def get_all_values(self, query: str = '.') -> List[Any]:
        full_path = self._path.concat(query)
        self._path_tracker.track(full_path)

        results = []
        for instance in reversed(self._data['metadata_instances']):
            payload = instance.get('payload', {})
            value = full_path.get_value(payload)

            if value is None:
                continue

            results.append(value)

        if len(results) == 0:
            if self._workflows_finished():
                raise ValueError(f'No data found for {query}')
            else:
                raise NoDataError(f'No data found for {query}')

        return results

    def __iter__(self):
        current_value = self.get_value()

        if isinstance(current_value, list):
            for i, item in enumerate(current_value):
                yield self.get_node(f'[{i}]')
            return

        if isinstance(current_value, dict):
            for key in current_value.keys():
                yield key
            return

        raise ValueError(f'Cannot iterate over scalar value: {type(current_value).__name__}')

    def items(self):
        current_value = self.get_value()

        if not isinstance(current_value, dict):
            raise ValueError('items() is only valid for dict-like data')

        for key in current_value.keys():
            yield (key, self.get_node(f'.{key}'))
