from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    # users 테이블을 문자열("users.id")로 참조하므로, users.models를 import할 필요는 없다.
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
