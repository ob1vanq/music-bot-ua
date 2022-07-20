import json
import logging
from dataclasses import dataclass
from typing import Union

from environs import Env
from sqlalchemy.engine import URL


class pay:
    def __init__(self):
        with open('app/data/details.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            self.paypal = data['paypal']
            self.card = data['card']


@dataclass
class Payment:
    paypal: str
    card: str


@dataclass
class TgBot:
    token: str
    admin_ids: tuple[int, ...]
    provider_token: str


@dataclass
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def sqlalchemy_url(self) -> URL:
        return URL.create(
            'postgresql+asyncpg',
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database
        )


@dataclass
class RedisConfig:
    host: str
    port: int


@dataclass
class Miscellaneous:
    log_level: int
    post_channel_chat_id: int
    photo_channel_chat_id: int
    sub_price: int
    logo: str

@dataclass
class Config:
    bot: TgBot
    db: DbConfig
    redis: RedisConfig
    misc: Miscellaneous
    payment: Payment

    @classmethod
    def from_env(cls, path: Union[str, None] = None) -> 'Config':
        env = Env()
        env.read_env(path)

        return Config(
            bot=TgBot(
                token=env.str('BOT_TOKEN'),
                admin_ids=tuple(map(int, env.list('ADMIN_IDS'))),
                provider_token=env.str('PROVIDER_TOKEN')
            ),
            db=DbConfig(
                host=env.str('DB_HOST', 'localhost'),
                port=env.int('DB_PORT', 5432),
                user=env.str('DB_USER', 'postgres'),
                password=env.str('DB_PASS', 'postgres'),
                database=env.str('DB_NAME', 'postgres'),
            ),
            redis=RedisConfig(
                host=env.str('REDIS_HOST', 'localhost'),
                port=env.int('REDIS_PORT', 6379),
            ),
            misc=Miscellaneous(
                log_level=env.log_level('LOG_LEVEL', logging.INFO),
                post_channel_chat_id=env.int('POST_CHANNEL_CHAT_ID'),
                photo_channel_chat_id=env.int('PHOTO_CHANNEL_CHAT_ID'),
                logo='app/data/logo.png',
                sub_price=env.int('SUBSCRIPTION_PRICE')
            ),
            payment=Payment(
                paypal=pay().paypal,
                card=pay().card
            )

        )
