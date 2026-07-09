from backend.models.models import User, DBConversation, DBMessage
from backend.models.growth_models import Subscription, UserLimitOverride
from sqlalchemy.orm import configure_mappers

try:
    configure_mappers()
    print("Mappers configured successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
