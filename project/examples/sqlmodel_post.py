"""SQLModel로 같은 게시글 한 줄을 메모리 SQLite에 넣는 예시.

본 앱의 모델은 SQLAlchemy다. 이 파일은 비교 학습용이며 앱이 import하지 않는다.
실행하려면 프로젝트 폴더에서 `pip install sqlmodel` 후 `python examples/sqlmodel_post.py`.
"""

from sqlmodel import Field, Session, SQLModel, create_engine, select


class Note(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str


def main() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Note(title="SQLModel 메모"))
        session.commit()
        row = session.exec(select(Note)).first()
        print(row.title if row else "empty")


if __name__ == "__main__":
    main()
