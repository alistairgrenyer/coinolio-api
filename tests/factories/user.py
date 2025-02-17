import factory
from app.models.user import User
from app.core.security import get_password_hash

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpassword123"))
    is_active = True
    subscription_tier = "FREE"
