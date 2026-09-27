import uuid
from sqlalchemy import Column, Integer, Text, Date, DateTime, ForeignKey, Numeric, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.db.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    source = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    license = Column(Text, nullable=True)
    coverage = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    crs = Column(Text, server_default="EPSG:4326")
    temporal_start = Column(Date, nullable=True)
    temporal_end = Column(Date, nullable=True)
    update_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())


class GeographicRegion(Base):
    __tablename__ = "geographic_regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    region_type = Column(Text, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("geographic_regions.id"), nullable=True, index=True)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)
    attributes = Column(JSONB, server_default="{}")

    parent = relationship("GeographicRegion", remote_side=[id])


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    feature_type = Column(Text, nullable=False, index=True)
    category = Column(Text, nullable=True, index=True)
    source_id = Column(Text, nullable=True)
    attributes = Column(JSONB, server_default="{}")
    geom = Column(Geometry("GEOMETRY", srid=4326), nullable=False)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    intent = Column(JSONB, nullable=True)
    plan = Column(JSONB, nullable=True)
    status = Column(Text, nullable=False, index=True)
    progress = Column(Integer, server_default="0")
    message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    vision_results = relationship("VisionResult", back_populates="analysis_run", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="analysis_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_analysis_runs_started_at_desc", started_at.desc()),
    )


class VisionResult(Base):
    __tablename__ = "vision_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    task_type = Column(Text, nullable=False)
    model_name = Column(Text, nullable=True)
    model_version = Column(Text, nullable=True)
    label = Column(Text, nullable=True)
    confidence = Column(Numeric, nullable=True)
    area_km2 = Column(Numeric, nullable=True)
    geom = Column(Geometry("GEOMETRY", srid=4326), nullable=True)
    metadata_ = Column("metadata", JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analysis_run = relationship("AnalysisRun", back_populates="vision_results")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    geojson = Column(JSONB, nullable=True)
    statistics = Column(JSONB, nullable=True)
    findings = Column(JSONB, nullable=True)
    insight = Column(JSONB, nullable=True)
    provenance = Column(JSONB, nullable=True)
    confidence = Column(JSONB, nullable=True)
    limitations = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analysis_run = relationship("AnalysisRun", back_populates="analysis_results")
