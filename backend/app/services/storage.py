import os
import uuid
from abc import ABC, abstractmethod
from typing import Tuple
from backend.app.core.config import settings


class StorageService(ABC):
    @abstractmethod
    def save_file(self, content: bytes, original_filename: str) -> Tuple[str, str]:
        pass

    @abstractmethod
    def get_file(self, stored_path: str) -> bytes:
        pass

    @abstractmethod
    def delete_file(self, stored_path: str) -> bool:
        pass

    @abstractmethod
    def file_exists(self, stored_path: str) -> bool:
        pass


class LocalDiskStorageService(StorageService):
    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, content: bytes, original_filename: str) -> Tuple[str, str]:
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        random_filename = f"{uuid.uuid4()}{ext}"
        full_path = os.path.join(self.base_dir, random_filename)
        with open(full_path, "wb") as f:
            f.write(content)
        return full_path, random_filename

    def get_file(self, stored_path: str) -> bytes:
        if not os.path.exists(stored_path):
            raise FileNotFoundError("Stored file not found")
        with open(stored_path, "rb") as f:
            return f.read()

    def delete_file(self, stored_path: str) -> bool:
        if os.path.exists(stored_path):
            try:
                os.remove(stored_path)
                return True
            except OSError:
                return False
        return False

    def file_exists(self, stored_path: str) -> bool:
        return os.path.exists(stored_path)


storage_service = LocalDiskStorageService()
