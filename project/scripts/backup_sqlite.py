"""SQLite 파일 하나를 날짜 이름으로 복사한다.

실행: python scripts/backup_sqlite.py
DATABASE_URL이 sqlite 파일이 아니면 아무것도 복사하지 않고 종료한다.
"""

import shutil
from datetime import datetime
from pathlib import Path

from app.config import get_settings


def main() -> None:
    url = get_settings().database_url
    if not url.startswith("sqlite:///"):
        print("sqlite 파일 URL이 아니라서 백업하지 않습니다.")
        return
    source = Path(url.removeprefix("sqlite:///"))
    if not source.exists():
        print(f"파일이 없습니다: {source}")
        return
    folder = Path("backups")
    folder.mkdir(exist_ok=True)
    target = folder / f"{source.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{source.suffix}"
    shutil.copy2(source, target)
    print(target)


if __name__ == "__main__":
    main()
