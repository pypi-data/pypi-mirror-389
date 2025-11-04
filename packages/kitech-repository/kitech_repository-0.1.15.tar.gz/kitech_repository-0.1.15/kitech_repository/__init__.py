"""KITECH Manufacturing Data Repository Library and CLI."""

__version__ = "0.1.14"
__author__ = "KITECH Repository Team"

from kitech_repository.core.auth import AuthManager
from kitech_repository.core.client import KitechClient
from kitech_repository.core.config import Config


# Convenience functions for library usage
def download(repository_id: int, path: str = "", output_dir: str = None, app_key: str = None):
    """Download a file or directory from repository.

    Args:
        repository_id: The repository ID
        path: Path within repository (empty string for root)
        output_dir: Local output directory (None for default)
        app_key: API app key (None to use stored app key)

    Returns:
        Path: Path to downloaded file/directory
    """
    with KitechClient(app_key=app_key) as client:
        return client.download_file(
            repository_id=repository_id, path=path if path else None, output_dir=output_dir, show_progress=True
        )


def upload_file(repository_id: int, file_path: str, remote_path: str = "", app_key: str = None):
    """Upload a single file to repository.

    Args:
        repository_id: The repository ID
        file_path: Local file path to upload
        remote_path: Remote path within repository (empty string for root)
        app_key: API app key (None to use stored app key)

    Returns:
        dict: Upload response data

    Raises:
        UploadError: If user has VIEWER role (no upload permission)
    """
    from pathlib import Path

    path = Path(file_path)

    if not path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    with KitechClient(app_key=app_key) as client:
        return client.upload_file(
            repository_id=repository_id, file_path=path, remote_path=remote_path, show_progress=True
        )


def upload(repository_id: int, file_path: str, remote_path: str = "", app_key: str = None):
    """Upload a file or folder to repository.

    Args:
        repository_id: The repository ID
        file_path: Local file or folder path to upload
        remote_path: Remote path within repository (empty string for root)
        app_key: API app key (None to use stored app key)

    Returns:
        dict: Upload response data (for file) or upload statistics (for folder)

    Raises:
        UploadError: If user has VIEWER role (no upload permission)
    """
    from pathlib import Path

    path = Path(file_path)

    if path.is_file():
        # Single file upload
        return upload_file(repository_id=repository_id, file_path=file_path, remote_path=remote_path, app_key=app_key)
    elif path.is_dir():
        # Folder upload
        return upload_folder(
            repository_id=repository_id, folder_path=file_path, remote_path=remote_path, app_key=app_key
        )
    else:
        raise ValueError(f"Path does not exist: {file_path}")


def list_repositories(app_key: str = None):
    """List available repositories.

    Args:
        app_key: API app key (None to use stored app key)

    Returns:
        list: List of Repository objects
    """
    with KitechClient(app_key=app_key) as client:
        result = client.list_repositories()
        return result["repositories"]


def upload_folder(repository_id: int, folder_path: str, remote_path: str = "", app_key: str = None):
    """Upload a folder and all its contents to repository.

    Args:
        repository_id: The repository ID
        folder_path: Local folder path to upload
        remote_path: Remote base path within repository
        app_key: API app key (None to use stored app key)

    Returns:
        dict: Upload statistics (uploaded count, failed count, file list)

    Raises:
        UploadError: If user has VIEWER role (no upload permission)
    """
    from pathlib import Path

    from kitech_repository.core.exceptions import UploadError

    folder = Path(folder_path)

    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder_path}")

    # Get all files in the folder
    files = list(folder.rglob("*"))
    files = [f for f in files if f.is_file()]

    uploaded = []
    failed = []

    with KitechClient(app_key=app_key) as client:
        # Check upload permission before starting (VIEWER role cannot upload)
        repos_result = client.list_repositories(page=0, limit=100)
        repository = next((r for r in repos_result["repositories"] if r.id == repository_id), None)

        if repository is None:
            raise UploadError(f"Repository {repository_id} not found")

        if repository.user_role == "VIEWER":
            raise UploadError(
                "Upload permission denied: You have VIEWER role. Only OWNER and ADMIN roles can upload files."
            )
        for file_path in files:
            relative_path = file_path.relative_to(folder)
            full_remote_path = f"{remote_path}/{relative_path}".replace("\\", "/").strip("/")

            try:
                client.upload_file(
                    repository_id=repository_id,
                    file_path=file_path,
                    remote_path=full_remote_path,
                    show_progress=False,
                    _skip_permission_check=True,  # Already checked above
                )
                uploaded.append(str(relative_path))
            except Exception as e:
                failed.append({"file": str(relative_path), "error": str(e)})

    return {
        "total": len(files),
        "uploaded": len(uploaded),
        "failed": len(failed),
        "uploaded_files": uploaded,
        "failed_files": failed,
    }


def list_files(repository_id: int, path: str = "", app_key: str = None, page: int = 0, limit: int = 100):
    """List files in repository.

    Args:
        repository_id: The repository ID
        path: Path within repository (empty string for root)
        app_key: API app key (None to use stored app key)
        page: Page number (default: 0)
        limit: Number of files per page (default: 100)

    Returns:
        dict: Dictionary containing 'files' list and pagination metadata
    """
    with KitechClient(app_key=app_key) as client:
        return client.list_files(repository_id, prefix=path if path else "", page=page, limit=limit)


# Export main classes and functions
__all__ = [
    "KitechClient",
    "AuthManager",
    "Config",
    "download",
    "upload",
    "upload_file",
    "upload_folder",
    "list_repositories",
    "list_files",
]
