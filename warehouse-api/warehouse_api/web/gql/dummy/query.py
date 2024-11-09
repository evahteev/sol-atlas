from typing import List

import strawberry
from strawberry.types import Info

from warehouse_api.db.dao.dummy_dao import DummyDAO
from warehouse_api.web.gql.context import Context
from warehouse_api.web.gql.dummy.schema import DummyModelDTO


@strawberry.type
class Query:
    """Query to interact with dummies."""

    @strawberry.field(description="Get all dummies")
    async def get_dummy_models(
        self,
        info: Info[Context, None],
        limit: int = 15,
        offset: int = 0,
    ) -> List[DummyModelDTO]:
        """
        Retrieves all dummy objects from database.

        :param info: connection info.
        :param limit: limit of dummy objects, defaults to 10.
        :param offset: offset of dummy objects, defaults to 0.
        :return: list of dummy objects from database.
        """
        dao = DummyDAO(info.context.db_connection)
        return await dao.get_all_dummies(limit=limit, offset=offset)  # type: ignore
