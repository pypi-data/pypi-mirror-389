from json import dump, load
from pathlib import Path
from threading import Lock


class AutoSaveList(list):
    def __init__(self, file_path: str):
        if Path(file_path).exists():
            super().__init__(load(open(file_path)))
        else:
            super().__init__()
        self.file_path = file_path
        self._lock = Lock()

    def save_to_file(self):
        with self._lock:
            with open(self.file_path, 'w') as f:
                dump(list(self), f)

    def append(self, item) -> None:
        super().append(item)
        self.save_to_file()

    def extend(self, items) -> None:
        super().extend(items)
        self.save_to_file()

    def pop(self, index: int = -1):
        item = super().pop(index)
        self.save_to_file()
        return item

    def remove(self, item) -> None:
        super().remove(item)
        self.save_to_file()

    def clear(self) -> None:
        super().clear()
        self.save_to_file()

    def __setitem__(self, key, value) -> None:
        super().__setitem__(key, value)
        self.save_to_file()

    def __delitem__(self, key) -> None:
        super().__delitem__(key)
        self.save_to_file()

    def index(self, value, start=0, stop=None) -> int:
        try:
            return super().index(value, start, stop if stop is not None else len(self))
        except ValueError:
            return -1
