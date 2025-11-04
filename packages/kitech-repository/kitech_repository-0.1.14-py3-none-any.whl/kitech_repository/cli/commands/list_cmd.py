"""List commands for CLI."""

import typer
from rich.console import Console
from rich.table import Table

from kitech_repository.cli.utils import get_cli_command_name
from kitech_repository.core.client import KitechClient
from kitech_repository.core.exceptions import AuthenticationError

console = Console()
app = typer.Typer()


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


@app.command(name="repos")
def list_repositories(
    page: int = typer.Option(0, "--page", "-p", help="Page number"),
    limit: int = typer.Option(20, "--limit", "-l", help="Items per page"),
    include_shared: bool = typer.Option(True, "--include-shared/--no-shared", help="Include shared repositories"),
):
    """List available repositories."""
    try:
        with KitechClient() as client:
            result = client.list_repositories(page=page, limit=limit, include_shared=include_shared)

            if not result["repositories"]:
                console.print("[yellow]No repositories found[/yellow]")
                return

            from rich.box import SQUARE

            table = Table(
                title="[bold]🗂️  전체 리포지토리[/bold]",
                show_header=True,
                header_style="bold cyan",
                box=SQUARE
            )
            table.add_column("ID", justify="right", style="dim")
            table.add_column("리포지토리 이름", style="bold")
            table.add_column("소유자")
            table.add_column("내 권한")
            table.add_column("설명", style="dim")

            # 권한 한국어 매핑
            role_map = {
                "OWNER": "소유자",
                "ADMIN": "관리자",
                "VIEWER": "뷰어",
                "NONE": "없음",
                None: "-"
            }

            for repo in result["repositories"]:
                table.add_row(
                    str(repo.id),
                    repo.name,
                    repo.owner_name,
                    role_map.get(repo.user_role, repo.user_role or "-"),
                    repo.description or "-"
                )

            console.print(table)

            # 페이지네이션 안내
            total_pages = (result['total_count'] + limit - 1) // limit
            current_page = page + 1

            console.print(f"\n{current_page}/{total_pages} (전체 {result['total_count']})")

            # 페이지 이동 명령어
            if total_pages > 1:
                cmd_name = get_cli_command_name()
                if page > 0:
                    console.print(f"이전 페이지: {cmd_name} list repos --page {page - 1}")
                if current_page < total_pages:
                    console.print(f"다음 페이지: {cmd_name} list repos --page {page + 1}")
    except AuthenticationError:
        console.print("[red]❌ Authentication required. Please login first with:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="files")
def list_files(
    repository_id: int = typer.Argument(..., help="Repository ID"),
    prefix: str = typer.Option("", "--prefix", "-p", help="Directory prefix to list"),
    search: str = typer.Option(None, "--search", "-s", help="Search for files matching pattern"),
):
    """List files in a repository."""
    try:
        with KitechClient() as client:
            result = client.list_files(repository_id=repository_id, prefix=prefix, search=search)

            if not result["files"]:
                console.print("[yellow]No files found[/yellow]")
                return

            console.print(f"📁 Repository #{repository_id} files")
            if prefix:
                console.print(f"📂 Path: {prefix}")
            if search:
                console.print(f"🔍 Search: {search}")
            console.print("-" * 60)

            for file in result["files"]:
                if file.is_directory:
                    console.print(f"📁 {file.name}/")
                else:
                    size_str = format_size(file.size)
                    console.print(f"📄 {file.name:<40} {size_str:>15}")

            console.print(f"\nTotal items: {result['total_count']}")
    except AuthenticationError:
        console.print("[red]❌ Authentication required. Please login first with:[/red]")
        console.print("  kitech auth login")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
