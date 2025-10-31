
from camunda_client.types_ import BaseSchema


class AddUserSchema(BaseSchema):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_admin: bool
    is_suspicious: bool
    telegram_user_id: int | None = None
    webapp_user_id: str | None = None
    is_block: bool | None = None
    is_premium: bool
    ref_user_id: str | None = None
