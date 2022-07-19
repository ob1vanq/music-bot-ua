import sqlalchemy as sa
from app.models.base import TimedBaseModel


class Track(TimedBaseModel):
    track_id = sa.Column(sa.INTEGER, primary_key=True, autoincrement=True)
    post_id = sa.Column(sa.INTEGER, sa.ForeignKey('posts.post_id', ondelete='SET NULL'), nullable=True)
    file_id = sa.Column(sa.VARCHAR(100), nullable=True)
    title = sa.Column(sa.VARCHAR(300), nullable=True)
    # is_paid = sa.Column(sa.BOOLEAN, nullable=False, default=False)
    price = sa.Column(sa.INTEGER, nullable=False, default=0)
