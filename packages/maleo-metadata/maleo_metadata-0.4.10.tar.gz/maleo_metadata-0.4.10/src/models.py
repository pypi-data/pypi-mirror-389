from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.types import Enum, String, UUID as SQLUUID
from uuid import UUID as PythonUUID, uuid4
from maleo.enums.service import ServiceCategory, ServiceType
from maleo.schemas.model import DataIdentifier, DataStatus, DataTimestamp
from maleo.types.integer import OptInt


class BloodType(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "blood_types"
    order: Mapped[OptInt] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(2), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(2), unique=True, nullable=False
    )


class Gender(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "genders"
    order: Mapped[OptInt] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )


class MedicalRole(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "medical_roles"
    parent_id: Mapped[OptInt] = mapped_column(
        "parent_id",
        ForeignKey("medical_roles.id", ondelete="SET NULL", onupdate="CASCADE"),
    )
    order: Mapped[OptInt] = mapped_column(name="order")
    code: Mapped[str] = mapped_column(
        name="code", type_=String(20), unique=True, nullable=False
    )
    key: Mapped[str] = mapped_column(
        name="key", type_=String(255), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(255), unique=True, nullable=False
    )

    @declared_attr
    def parent(cls) -> Mapped["MedicalRole | None"]:
        return relationship(
            back_populates="children", remote_side="MedicalRole.id", lazy="select"
        )

    @declared_attr
    def children(cls) -> Mapped[list["MedicalRole"]]:
        return relationship(
            back_populates="parent",
            cascade="all, delete-orphan",
            lazy="select",
            order_by="MedicalRole.order",
        )


class MedicalService(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "medical_services"
    order: Mapped[OptInt] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )


class OrganizationRole(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "organization_roles"
    order: Mapped[OptInt] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )


class OrganizationType(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "organization_types"
    order: Mapped[OptInt] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )


class Service(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "services"
    order: Mapped[OptInt] = mapped_column(name="order")
    type: Mapped[ServiceType] = mapped_column(
        name="type", type_=Enum(ServiceType, name="service_type"), nullable=False
    )
    category: Mapped[ServiceCategory] = mapped_column(
        name="category",
        type_=Enum(ServiceCategory, name="service_category"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )
    secret: Mapped[PythonUUID] = mapped_column(
        "secret", SQLUUID(as_uuid=True), default=uuid4, unique=True, nullable=False
    )


class SystemRole(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "system_roles"
    order: Mapped[OptInt] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )


class UserType(
    DataTimestamp,
    DataStatus,
    DataIdentifier,
):
    __tablename__ = "user_types"
    order: Mapped[OptInt] = mapped_column(name="order")
    key: Mapped[str] = mapped_column(
        name="key", type_=String(20), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        name="name", type_=String(20), unique=True, nullable=False
    )
