"""Test cases for the base repository"""
from datetime import datetime, timezone

import pytest
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String

from app.db.base_class import Base
from app.repositories.base import BaseRepository


# Test models
class TestModel(Base):
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class TestModelCreate(BaseModel):
    name: str

class TestModelUpdate(BaseModel):
    name: str

class TestRepository(BaseRepository[TestModel, TestModelCreate, TestModelUpdate]):
    pass

@pytest.fixture
def test_repo():
    """Create a test repository"""
    return TestRepository(TestModel)

@pytest.fixture
def test_model(db_session):
    """Create a test model instance"""
    model = TestModel(name="test")
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model

class TestBaseRepository:
    """Test cases for BaseRepository"""

    def test_get(self, test_repo, test_model, db_session):
        """Test getting a model by ID"""
        result = test_repo.get(db_session, test_model.id)
        assert result.id == test_model.id
        assert result.name == test_model.name

    def test_get_non_existent(self, test_repo, db_session):
        """Test getting a non-existent model"""
        result = test_repo.get(db_session, 999)
        assert result is None

    def test_get_multi(self, test_repo, db_session):
        """Test getting multiple models"""
        # Create test data
        models = [
            TestModel(name=f"test_{i}")
            for i in range(3)
        ]
        for model in models:
            db_session.add(model)
        db_session.commit()

        # Test pagination
        results = test_repo.get_multi(db_session, skip=1, limit=2)
        assert len(results) == 2
        assert results[0].name == "test_1"
        assert results[1].name == "test_2"

    def test_create(self, test_repo, db_session):
        """Test creating a new model"""
        model_in = TestModelCreate(name="new_test")
        result = test_repo.create(db_session, obj_in=model_in)
        assert result.name == "new_test"
        assert result.id is not None

    def test_update(self, test_repo, test_model, db_session):
        """Test updating a model"""
        update_data = TestModelUpdate(name="updated_test")
        result = test_repo.update(db_session, db_obj=test_model, obj_in=update_data)
        assert result.name == "updated_test"
        assert result.id == test_model.id

    def test_update_with_dict(self, test_repo, test_model, db_session):
        """Test updating a model with a dictionary"""
        update_data = {"name": "updated_test"}
        result = test_repo.update(db_session, db_obj=test_model, obj_in=update_data)
        assert result.name == "updated_test"
        assert result.id == test_model.id

    def test_delete(self, test_repo, test_model, db_session):
        """Test deleting a model"""
        test_repo.delete(db_session, id=test_model.id)
        result = test_repo.get(db_session, test_model.id)
        assert result is None
