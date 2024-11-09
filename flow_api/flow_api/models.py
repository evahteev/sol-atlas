import datetime
import uuid
from typing import Optional, Iterable

from tortoise import Model, fields, BaseDBAsyncClient
from tortoise.fields.relational import ForeignKeyRelation

from flow_api.art_models import ArtCollection, Art
from flow_api.enums import Status
from flow_api.flow_models import ExternalWorker, Strategy, Invite, Flow
from fastapi_admin.models import AbstractAdmin


class Role(Model):
    name = fields.CharField(max_length=80, unique=True)
    description = fields.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Admin(AbstractAdmin):
    id = fields.IntField(pk=True)
    last_login = fields.DatetimeField(
        description="Last Login", default=datetime.datetime.now
    )
    email = fields.CharField(max_length=200, default="")
    avatar = fields.CharField(max_length=200, default="")
    intro = fields.TextField(default="")
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pk}#{self.username}"

    def _pre_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
    ):
        if isinstance(self.created_at, datetime.datetime):
            self.created_at = self.created_at.replace(tzinfo=None)
        return super()._pre_save(using_db=using_db, update_fields=update_fields)


class User(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    username = fields.CharField(max_length=200, null=True)
    first_name = fields.CharField(max_length=200, null=True)
    last_name = fields.CharField(max_length=200, null=True)
    email = fields.CharField(max_length=200, null=True)
    language_code = fields.CharField(max_length=10, null=True)
    is_admin = fields.BooleanField()
    is_suspicious = fields.BooleanField()
    camunda_user_id = fields.CharField(max_length=36, null=True)
    camunda_key = fields.UUIDField(default=uuid.uuid4, null=True)
    telegram_user_id = fields.BigIntField(null=True)
    discord_user_id = fields.CharField(max_length=200, null=True)
    webapp_user_id = fields.UUIDField(default=uuid.uuid4, null=True)
    is_block = fields.BooleanField()
    is_premium = fields.BooleanField()
    created_at = fields.DatetimeField(
        auto_now_add=True, default=datetime.datetime.utcnow
    )
    roles = fields.ManyToManyField("models.Role", related_name="user", default=[])
    strategies: ForeignKeyRelation["Strategy"]
    flows: ForeignKeyRelation["Flow"]
    external_workers: ForeignKeyRelation["ExternalWorker"]
    arts: ForeignKeyRelation["Art"]
    art_collections: ForeignKeyRelation["ArtCollection"]
    invites: ForeignKeyRelation["Invite"]
    web3_wallets: ForeignKeyRelation["Web3User"]
    telegram_accounts: ForeignKeyRelation["TelegramUser"]


class Config(Model):
    label = fields.CharField(max_length=200)
    key = fields.CharField(
        max_length=20, unique=True, description="Unique key for config"
    )
    value = fields.JSONField()
    status: Status = fields.IntEnumField(Status, default=Status.on)


class Web3User(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    wallet_address = fields.CharField(max_length=255)
    network_type = fields.CharField(max_length=50)
    private_key = fields.CharField(max_length=300, null=True, default=None)
    user: ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="web3_wallets"
    )

    class Meta:
        table = "web3_users"

    def __str__(self):
        return f"{self.wallet_address} on {self.network_type}"

    def dict(self):
        return {
            "id": self.id,
            "wallet_address": self.wallet_address,
            "network_type": self.network_type,
            "private_key": self.private_key,
        }


class TelegramUser(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    telegram_id = fields.BigIntField()
    is_premium = fields.BooleanField(default=False)
    user: ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="telegram_accounts", on_delete=fields.CASCADE
    )

    class Meta:
        table = "telegram_users"

    def __str__(self):
        return f"Telegram ID: {self.telegram_id}, Premium: {self.is_premium}"
