"""
Local panel widget for displaying local filesystem.

This widget shows the current directory's files in a flat DataTable structure,
allowing navigation, file selection, and upload operations.
"""

from pathlib import Path

from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Static


class LocalPanel(Container):
    """
    Panel for browsing local filesystem.

    Features:
    - DataTable widget for flat directory display (current directory only)
    - Reactive focus management with visual indicators
    - Current path tracking (明確な現在位置)
    - Enter key to navigate into folders
    - Backspace key to go to parent directory
    - Upload operations (F3: upload all, F4: upload selected)
    """

    # Allow this container to receive keyboard focus
    can_focus = True

    # Reactive properties
    has_focus: reactive[bool] = reactive(False)
    current_path: reactive[Path] = reactive(Path.cwd())
    is_loading: reactive[bool] = reactive(False)

    DEFAULT_CSS = """
    LocalPanel {
        border: solid $primary;
        height: 1fr;
        width: 1fr;
    }

    LocalPanel.focused {
        border: solid yellow;
    }

    LocalPanel Static {
        background: $boost;
        color: $text;
        padding: 0 1;
    }

    LocalPanel DataTable {
        background: $surface;
        height: 1fr;
    }

    LocalPanel #error-message {
        color: red;
        margin: 1 2;
        text-align: center;
    }
    """

    BINDINGS = [
        ("f3", "upload_all", "전체 업로드"),
        ("f4", "upload_selected", "선택 업로드"),
        ("f5", "refresh", "새로고침"),
        ("backspace", "go_parent", "상위 디렉토리"),
    ]

    def __init__(self, user_role: str | None = None, **kwargs):
        """
        Initialize the local panel.

        Args:
            user_role: User's role in the repository (OWNER, ADMIN, VIEWER, NONE)
            **kwargs: Additional arguments passed to Container
        """
        super().__init__(**kwargs)
        self.user_role = user_role
        self._files: list[Path] = []

    def _is_operation_in_progress(self) -> bool:
        """
        Check if there's a file operation currently in progress.

        Checks the FileManagerScreen's global flag to prevent any operation
        (upload or download) from starting while another is active.

        Returns:
            True if any operation is active
        """
        try:
            from kitech_repository.tui.screens.file_manager import FileManagerScreen

            # Check global flag on FileManagerScreen
            if isinstance(self.screen, FileManagerScreen):
                return self.screen.is_operation_active
            return False
        except Exception:
            return False

    def compose(self):
        """Compose the local panel UI."""
        yield Static(f"Local: {self.current_path}", id="local-header", classes="panel-header")
        # Use DataTable to display files (flat structure)
        table = DataTable(id="local-table", cursor_type="row")
        table.add_columns("", "이름", "크기")
        yield table

    def on_key(self, event) -> None:
        """
        Handle key events for the local panel.

        This handler catches F3/F4 keys even when DataTable has focus.
        """
        if event.key == "f3":
            event.prevent_default()
            event.stop()
            self.action_upload_all()
        elif event.key == "f4":
            event.prevent_default()
            event.stop()
            # Call async action using run_worker
            self.run_worker(self.action_upload_selected())

    def on_mount(self) -> None:
        """Initialize panel when mounted."""
        self._update_header()
        self.load_files()

    def watch_has_focus(self, old: bool, new: bool) -> None:
        """
        React to focus changes.

        Updates the CSS class to show/hide visual focus indicator.

        Args:
            old: Previous focus state
            new: New focus state
        """
        if new:
            self.add_class("focused")
        else:
            self.remove_class("focused")

    def watch_current_path(self, old: Path, new: Path) -> None:
        """
        React to current path changes.

        Reloads the directory listing when path changes.

        Args:
            old: Previous path
            new: New path
        """
        if old != new:
            self._update_header()
            if self.is_mounted:
                self.load_files()

    def _update_header(self) -> None:
        """Update the header with current path."""
        try:
            header = self.query_one("#local-header", Static)
            header.update(f"Local: {self.current_path}")
        except Exception:
            # Header might not be mounted yet
            pass

    def load_files(self) -> None:
        """
        Load file list from current directory.

        Lists only the files and folders in the current directory (flat, non-recursive).
        Handles permission errors with actionable messages.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # List files in current directory
            self._files = sorted(
                self.current_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower())  # Directories first, then alphabetical
            )

            # Populate DataTable
            table = self.query_one("#local-table", DataTable)
            table.clear()

            # Add ".." entry if not at root
            if self.current_path.parent != self.current_path:
                table.add_row("📁", "..", "-")

            for file_path in self._files:
                # Determine file type icon
                if file_path.is_dir():
                    file_type = "📁"
                    size_str = "-"
                elif file_path.is_file():
                    file_type = "📄"
                    # Get file size
                    try:
                        size_bytes = file_path.stat().st_size
                        if size_bytes < 1024:
                            size_str = f"{size_bytes} B"
                        elif size_bytes < 1024 * 1024:
                            size_str = f"{size_bytes / 1024:.1f} KB"
                        else:
                            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                    except Exception:
                        size_str = "?"
                else:
                    file_type = "❓"
                    size_str = "?"

                # Add row to table
                table.add_row(file_type, file_path.name, size_str)

            # Success - clear any error messages
            try:
                error_widget = self.query_one("#error-message", Static)
                error_widget.remove()
            except Exception:
                pass  # No error message to remove

        except PermissionError:
            # Permission denied - show actionable message
            logger.error(f"Permission denied: {self.current_path}")
            self._show_error(
                f"Permission Denied\n\n"
                f"You don't have permission to access: {self.current_path}\n\n"
                f"Action: Press Backspace to go to parent directory."
            )

        except OSError as e:
            # File system error - show actionable message
            logger.error(f"File system error: {e}")
            self._show_error(
                f"File System Error\n\n"
                f"Cannot access: {self.current_path}\n"
                f"Error: {str(e)}\n\n"
                f"Action: Press Backspace to go to parent directory."
            )

        except Exception as e:
            logger.error(f"Unexpected error loading files: {e}")
            self._show_error(f"Error: {str(e)}\n\nAction: Press F5 to retry.")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        try:
            error_widget = self.query_one("#error-message", Static)
            error_widget.update(message)
        except Exception:
            # Error widget doesn't exist, create it
            self.mount(Static(message, id="error-message"))

    async def action_refresh(self) -> None:
        """
        Handle refresh action (F5 key).

        Reloads the current directory listing.
        """
        self.load_files()

    def on_file_operation_completed(self, message) -> None:
        """
        Handle file operation completed message.

        Auto-refresh the file list when an upload completes.

        Args:
            message: FileOperationCompleted message
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"LocalPanel: File operation completed, refreshing file list")

        # Save current cursor position before refresh
        table = self.query_one("#local-table", DataTable)
        saved_cursor_row = table.cursor_row

        # Auto-refresh after any file operation completes
        self.load_files()

        # Restore cursor position after refresh
        if saved_cursor_row is not None and saved_cursor_row >= 0:
            try:
                table.move_cursor(row=saved_cursor_row)
            except Exception:
                pass  # Cursor position might be out of range after refresh

    async def action_go_parent(self) -> None:
        """
        Handle go parent action (Backspace key).

        Navigates to the parent directory.
        """
        if self.current_path.parent != self.current_path:
            self.current_path = self.current_path.parent

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Handle DataTable row selection (Enter key or click).

        If a folder is selected, navigate into it.
        If ".." is selected, navigate to parent directory.

        Args:
            event: RowSelected event from DataTable
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get the row index
        row_index = event.cursor_row

        if row_index is None or row_index < 0:
            return  # No file selected

        # Check if ".." was selected (first row when not at root)
        has_parent_entry = self.current_path.parent != self.current_path
        if has_parent_entry and row_index == 0:
            # Navigate to parent directory
            logger.info("'..' selected, navigating to parent directory")
            self.current_path = self.current_path.parent
            return

        # Adjust index for ".." entry
        file_index = row_index - 1 if has_parent_entry else row_index

        # Get file from internal list
        if file_index < 0 or file_index >= len(self._files):
            logger.warning(f"Invalid file index: {file_index}, files count: {len(self._files)}")
            return  # Invalid selection

        selected_path = self._files[file_index]
        logger.info(f"Row selected: {selected_path}, is_dir: {selected_path.is_dir()}")

        # Only navigate into directories
        if selected_path.is_dir():
            self.current_path = selected_path

    async def action_upload_selected(self) -> None:
        """
        Handle upload selected file or folder action (F4 key).

        Posts FileOperationStarted message for the selected file or folder.
        If a folder is selected, it uploads the entire folder with its structure.
        Uploads to the remote panel's current directory.
        """
        import uuid

        # Check if user has upload permission
        if self.user_role == "VIEWER":
            self.app.notify("업로드 권한이 없습니다. (뷰어 권한)", severity="error", timeout=2)
            return

        # Check if another operation is already in progress
        if self._is_operation_in_progress():
            return

        from kitech_repository.tui.messages import FileOperationStarted
        from kitech_repository.tui.models import FileOperation, OperationStatus

        # Get selected file from table
        table = self.query_one("#local-table", DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return  # No file selected

        # Check if ".." is selected (cannot upload parent directory marker)
        has_parent_entry = self.current_path.parent != self.current_path
        if has_parent_entry and table.cursor_row == 0:
            return  # Skip if ".." is selected

        # Adjust index for ".." entry
        file_index = table.cursor_row - 1 if has_parent_entry else table.cursor_row

        # Get file from internal list
        if file_index < 0 or file_index >= len(self._files):
            return  # Invalid selection

        selected_path = self._files[file_index]

        # Determine operation type based on whether it's a file or directory
        if selected_path.is_dir():
            operation_type = "upload_all"  # Use upload_all for folders
        elif selected_path.is_file():
            operation_type = "upload"
        else:
            return  # Skip if neither file nor directory

        # Get remote panel's current path to upload to
        try:
            from kitech_repository.tui.widgets.remote_panel import RemotePanel
            remote_panel = self.screen.query_one("#remote-panel", RemotePanel)
            remote_path = remote_panel.current_path
        except Exception:
            remote_path = ""  # Fallback to root if unable to get remote path

        # Create file operation
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=operation_type,
            file_path=str(selected_path),
            local_path=str(selected_path),
            remote_path=remote_path,  # Upload to remote panel's current directory
            status=OperationStatus.PENDING,
            progress_percent=0.0,
        )

        # Post message to start operation
        self.post_message(FileOperationStarted(operation=operation))

    def action_upload_all(self) -> None:
        """
        Handle upload all files action (F3 key).

        Shows confirmation dialog before starting batch upload of all files in current directory.
        """
        # Check if user has upload permission
        if self.user_role == "VIEWER":
            self.app.notify("업로드 권한이 없습니다. (뷰어 권한)", severity="error", timeout=2)
            return

        # Run in worker context to allow push_screen_wait
        self.run_worker(self._upload_all_worker())

    async def _upload_all_worker(self) -> None:
        """Worker for upload all operation. Uploads to remote panel's current directory."""
        import uuid

        # Check if another operation is already in progress
        if self._is_operation_in_progress():
            return

        from kitech_repository.tui.messages import FileOperationStarted
        from kitech_repository.tui.models import FileOperation, OperationStatus
        from kitech_repository.tui.widgets.confirmation_dialog import ConfirmationDialog

        # Get remote panel's current path to show in confirmation
        try:
            from kitech_repository.tui.widgets.remote_panel import RemotePanel
            remote_panel = self.screen.query_one("#remote-panel", RemotePanel)
            remote_path = remote_panel.current_path
            repository_name = remote_panel.repository_name

            # Build location display
            location = f"/{remote_path}" if remote_path else "/"
        except Exception:
            remote_path = ""
            repository_name = "알 수 없음"
            location = "/"

        # Show confirmation dialog
        confirmed = await self.app.push_screen_wait(
            ConfirmationDialog(
                f"전체 업로드를 진행하시겠습니까?\n\n"
                f"리포지토리 이름: {repository_name}\n"
                f"위치: {location}"
            )
        )

        if not confirmed:
            return  # User cancelled

        # Upload all files in current directory (non-recursive)
        # Create a batch operation for the current directory
        # Use "upload_current_dir" to distinguish from F4 (upload selected folder)
        operation = FileOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="upload_current_dir",
            file_path=str(self.current_path),
            local_path=str(self.current_path),
            remote_path=remote_path,  # Upload to remote panel's current directory
            status=OperationStatus.PENDING,
            progress_percent=0.0,
        )

        # Post message to start operation
        self.post_message(FileOperationStarted(operation=operation))
