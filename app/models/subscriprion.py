import sqlalchemy as sa

from app.models.base import TimedBaseModel


class Subscription(TimedBaseModel):
    sub_id = sa.Column(sa.INTEGER, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.INTEGER, sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=False)
    status = sa.Column(sa.BOOLEAN, nullable=False, default=False)
    last_paid = sa.Column(sa.DateTime, nullable=True)
