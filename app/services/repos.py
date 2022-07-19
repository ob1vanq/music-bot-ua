from datetime import datetime

from app.models import *
from app.models.subscriprion import Subscription
from app.models.track import Track
from app.services.db_ctx import BaseRepo


class UserRepo(BaseRepo[User]):
    model = User

    async def get_user(self, user_id: int) -> User | None:
        model = self.model
        return await self.get_one(model.user_id == user_id)

    async def update_user(self, user_id: int, **kwargs) -> None:
        return await self.update(self.model.user_id == user_id, **kwargs)


class PostRepo(BaseRepo[Post]):
    model = Post

    async def update_post(self, post_id: int, **kwargs) -> None:
        return await self.update(self.model.post_id == post_id, **kwargs)

    async def get_post_by_post_id(self, post_id: int) -> Post:
        return await self.get_one(self.model.post_id == post_id)


class TrackRepo(BaseRepo[Track]):
    model = Track

    async def get_tracks_by_post_id(self, post_id: int) -> list[Track]:
        return await self.get_all(self.model.post_id == post_id)

    async def get_tracks_by_track_id(self, track_id: int) -> Track:
        return await self.get_one(self.model.track_id == track_id)

    async def update_track(self, track_id: int, **kwargs):
        return await self.update(self.model.track_id == track_id, **kwargs)


class SubscriptRepo(BaseRepo[Subscription]):
    model = Subscription

    async def get_active_users(self) -> list[Subscription]:
        return await self.get_all(self.model.status == True)

    async def update_subscript(self, user_id: int, **kwargs):
        return await self.update(self.model.user_id == user_id, **kwargs)

    async def get_sub_by_user_id(self, user_id: int) -> Subscription:
        return await self.get_one(self.model.user_id == user_id)

    async def update_date_by_user_id(self, user_id: int):
        return await self.update(self.model.user_id == user_id, last_paid=datetime.now())


__all__ = (
    'UserRepo',
    'PostRepo',
    'TrackRepo',
    'SubscriptRepo'
)
