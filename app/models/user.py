import sqlalchemy as sa

from app.models.base import TimedBaseModel


class User(TimedBaseModel):
    user_id = sa.Column(sa.BIGINT, primary_key=True, autoincrement=False, index=True)
    mention = sa.Column(sa.VARCHAR(300), nullable=False)
    # subscription = sa.Column(sa.BOOLEAN, nullable=False, default=False)


