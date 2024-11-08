"""Redis API."""
from warehouse_api.web.gql.redis.mutation import Mutation
from warehouse_api.web.gql.redis.query import Query

__all__ = ["Query", "Mutation"]
