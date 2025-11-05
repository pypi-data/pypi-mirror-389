"""This module provides the service for the FeatureName feature."""
from typing import List, Dict, Set, Generic, Type

from sqlalchemy import func
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.lib.base_model_service import BaseModelService

from ..models.feature_name import FeatureName, FeatureNameCreate, FeatureNameLoad, FeatureNameUpdate

class FeatureNameService(BaseModelService[FeatureName, FeatureNameCreate, FeatureNameLoad, FeatureNameUpdate]):
    """The service for the FeatureName feature.

    This class inherits from BaseModelService and provides the business logic for the FeatureName feature.
    """
    def __init__(self, model: Type[FeatureName], create_schema: Type[FeatureNameCreate], load_schema: Type[FeatureNameLoad], update_schema: Type[FeatureNameUpdate]):
        """Initializes the FeatureNameService.

        Args:
            model: The FeatureName model.
            create_schema: The FeatureNameCreate schema.
            load_schema: The FeatureNameLoad schema.
            update_schema: The FeatureNameUpdate schema.
        """
        super().__init__(model, create_schema, load_schema, update_schema)