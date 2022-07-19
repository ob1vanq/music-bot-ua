import sqlalchemy as sa

from app.models.base import TimedBaseModel


class Post(TimedBaseModel):
    post_id = sa.Column(sa.INTEGER, primary_key=True, autoincrement=True)
    type = sa.Column(sa.VARCHAR(30), nullable=True)
    year = sa.Column(sa.VARCHAR(10), nullable=True)
    photo_id = sa.Column(sa.VARCHAR(100), nullable=True)
