import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Graph(Base):
    __tablename__ = "graphs"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    entry_node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"), nullable=True)
    source_path: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    nodes: Mapped[list["Node"]] = relationship(
        back_populates="graph",
        foreign_keys="Node.graph_id",
    )
    branches: Mapped[list["Branch"]] = relationship(back_populates="graph")
    sessions: Mapped[list["Session"]] = relationship(back_populates="graph")
    entry_node: Mapped["Node | None"] = relationship(foreign_keys=[entry_node_id])


class Node(Base):
    __tablename__ = "nodes"
    __table_args__ = (UniqueConstraint("graph_id", "slug", name="uq_node_graph_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("graphs.id"), index=True)
    slug: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(256))
    content_md: Mapped[str] = mapped_column(Text, default="")
    node_type: Mapped[str] = mapped_column(String(64), default="content")
    sort_order: Mapped[int] = mapped_column(default=0)

    graph: Mapped["Graph"] = relationship(
        back_populates="nodes",
        foreign_keys=[graph_id],
    )
    assets: Mapped[list["Asset"]] = relationship(back_populates="node")
    outgoing_branches: Mapped[list["Branch"]] = relationship(
        back_populates="from_node",
        foreign_keys="Branch.from_node_id",
    )
    incoming_branches: Mapped[list["Branch"]] = relationship(
        back_populates="to_node",
        foreign_keys="Branch.to_node_id",
    )


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("graphs.id"), index=True)
    from_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), index=True)
    to_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), index=True)
    label: Mapped[str] = mapped_column(String(256))
    sort_order: Mapped[int] = mapped_column(default=0)

    graph: Mapped["Graph"] = relationship(back_populates="branches")
    from_node: Mapped["Node"] = relationship(
        back_populates="outgoing_branches",
        foreign_keys=[from_node_id],
    )
    to_node: Mapped["Node"] = relationship(
        back_populates="incoming_branches",
        foreign_keys=[to_node_id],
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String(512))
    alt_text: Mapped[str] = mapped_column(String(256), default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

    node: Mapped["Node"] = relationship(back_populates="assets")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    graph_id: Mapped[int] = mapped_column(ForeignKey("graphs.id"), index=True)
    current_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    graph: Mapped["Graph"] = relationship(back_populates="sessions")
    current_node: Mapped["Node"] = relationship(foreign_keys=[current_node_id])
