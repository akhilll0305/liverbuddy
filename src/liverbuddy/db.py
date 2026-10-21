"""Persistence: SQLAlchemy 2.0 models (SQLite by default, Postgres via LB_DATABASE_URL)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from functools import lru_cache

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from liverbuddy.scoring.clinical import PatientMeasures


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100), default="")
    sex: Mapped[str | None] = mapped_column(String(10))
    birth_year: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    asian_ethnicity: Mapped[bool] = mapped_column(default=False)
    type2_diabetes: Mapped[bool] = mapped_column(default=False)
    on_antihypertensives: Mapped[bool] = mapped_column(default=False)
    on_lipid_lowering: Mapped[bool] = mapped_column(default=False)
    alcohol_g_per_week: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    labs: Mapped[list[LabResult]] = relationship(back_populates="user", cascade="all, delete-orphan")
    measurements: Mapped[list[Measurement]] = relationship(back_populates="user", cascade="all, delete-orphan")
    meals: Mapped[list[MealLog]] = relationship(back_populates="user", cascade="all, delete-orphan")
    medications: Mapped[list[Medication]] = relationship(back_populates="user", cascade="all, delete-orphan")


class LabResult(Base):
    __tablename__ = "lab_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    taken_on: Mapped[date] = mapped_column(Date)
    values: Mapped[dict] = mapped_column(JSON)  # analyte -> value in score units
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual | report
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    user: Mapped[User] = relationship(back_populates="labs")


class Measurement(Base):
    __tablename__ = "measurements"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    taken_on: Mapped[date] = mapped_column(Date)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    waist_cm: Mapped[float | None] = mapped_column(Float)
    systolic_bp: Mapped[float | None] = mapped_column(Float)
    diastolic_bp: Mapped[float | None] = mapped_column(Float)
    user: Mapped[User] = relationship(back_populates="measurements")


class MealLog(Base):
    __tablename__ = "meals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    description: Mapped[str] = mapped_column(String(1000), default="")
    score: Mapped[int] = mapped_column(Integer)
    kcal: Mapped[float] = mapped_column(Float)
    analysis: Mapped[dict] = mapped_column(JSON)
    user: Mapped[User] = relationship(back_populates="meals")


class Medication(Base):
    __tablename__ = "medications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    dose_text: Mapped[str] = mapped_column(String(200), default="")
    livertox_name: Mapped[str | None] = mapped_column(String(200))
    likelihood: Mapped[str | None] = mapped_column(String(4))
    active: Mapped[bool] = mapped_column(default=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    user: Mapped[User] = relationship(back_populates="medications")


@lru_cache
def get_sessionmaker(url: str) -> sessionmaker[Session]:
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


def latest_measures(db: Session, user: User, today: date | None = None) -> PatientMeasures:
    """Merge profile + most recent value of every lab analyte and body measurement."""
    today = today or date.today()
    labs: dict[str, float] = {}
    for lab in db.scalars(select(LabResult).where(LabResult.user_id == user.id).order_by(LabResult.taken_on)):
        labs.update({k: v for k, v in lab.values.items() if v is not None})
    body: dict[str, float] = {}
    for m in db.scalars(select(Measurement).where(Measurement.user_id == user.id).order_by(Measurement.taken_on)):
        body.update({k: getattr(m, k) for k in ("weight_kg", "waist_cm", "systolic_bp", "diastolic_bp")
                     if getattr(m, k) is not None})
    return PatientMeasures(
        age=today.year - user.birth_year if user.birth_year else None, sex=user.sex, height_cm=user.height_cm,
        asian_ethnicity=user.asian_ethnicity, type2_diabetes=user.type2_diabetes,
        on_antihypertensives=user.on_antihypertensives, on_lipid_lowering=user.on_lipid_lowering,
        alcohol_g_per_week=user.alcohol_g_per_week, **body, **labs)


def lab_timeline(db: Session, user: User) -> list[dict]:
    """One row per lab date with the values known *as of* that date, for trend charts."""
    rows, running = [], {}
    for lab in db.scalars(select(LabResult).where(LabResult.user_id == user.id).order_by(LabResult.taken_on)):
        running.update({k: v for k, v in lab.values.items() if v is not None})
        rows.append({"taken_on": lab.taken_on.isoformat(), **running})
    return rows
