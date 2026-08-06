from sqlalchemy.ext.asyncio import AsyncSession
import json
from app.models.workflow import Activity

async def log_activity(db: AsyncSession, project_id: int, user_id: int, action: str, entity_type: str = None, entity_id: int = None, metadata: dict = None):
    """
    Logs an action to the activities audit trail.
    """
    activity = Activity(
        project_id=project_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata) if metadata else None
    )
    db.add(activity)
    await db.commit()
    return activity
