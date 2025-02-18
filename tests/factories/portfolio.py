import factory
from datetime import datetime, timezone
import random
from app.models.portfolio import Portfolio, PortfolioVersion

class PortfolioFactory(factory.Factory):
    class Meta:
        model = Portfolio
        exclude = ('_sa_instance_state',)

    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    is_cloud_synced = False
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    version = 1
    total_value_usd = factory.LazyFunction(lambda: 75000.0)  # 1.5 BTC * 35000 + 10 ETH * 2500
    asset_count = 2
    user_id = None  # This should be set when creating instances
    last_sync_at = None
    last_sync_device = None
    had_conflicts = False
    pending_changes = 0
    data = factory.LazyFunction(lambda: {
        "assets": {
            "bitcoin": {
                "amount": "1.5",
                "cost_basis": "35000.00",
                "notes": "Initial investment"
            },
            "ethereum": {
                "amount": "10.0",
                "cost_basis": "2500.00",
                "notes": "DCA strategy"
            }
        },
        "settings": {
            "default_currency": "USD",
            "price_alerts": True
        },
        "metadata": {
            "created_from": "web",
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        "schema_version": "1.0.0"
    })

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle SQLAlchemy session state"""
        if '_sa_instance_state' in kwargs:
            kwargs.pop('_sa_instance_state')
        return super()._create(model_class, *args, **kwargs)

    @factory.post_generation
    def setup_sync_fields(obj, create, extracted, **kwargs):
        """Set up sync-related fields if is_cloud_synced is True"""
        if obj.is_cloud_synced:
            obj.last_sync_at = obj.last_sync_at or datetime.now(timezone.utc)
            obj.last_sync_device = obj.last_sync_device or "test_device"
            obj.had_conflicts = obj.had_conflicts or False
            obj.pending_changes = obj.pending_changes or 0

class PortfolioVersionFactory(factory.Factory):
    class Meta:
        model = PortfolioVersion
        exclude = ('_sa_instance_state',)

    version = factory.Sequence(lambda n: n + 1)
    portfolio_id = None  # This should be set when creating instances
    total_value_usd = factory.LazyFunction(lambda: 52500.0)  # 1.5 BTC * 35000
    asset_count = 1
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    data = factory.LazyFunction(lambda: {
        "assets": {
            "bitcoin": {
                "amount": "1.5",
                "cost_basis": "35000.00"
            }
        },
        "settings": {"default_currency": "USD"},
        "metadata": {
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        "schema_version": "1.0.0"
    })
    change_summary = factory.LazyFunction(lambda: {
        "added_assets": [],
        "removed_assets": [],
        "modified_assets": ["bitcoin"]
    })

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle SQLAlchemy session state"""
        if '_sa_instance_state' in kwargs:
            kwargs.pop('_sa_instance_state')
        return super()._create(model_class, *args, **kwargs)
