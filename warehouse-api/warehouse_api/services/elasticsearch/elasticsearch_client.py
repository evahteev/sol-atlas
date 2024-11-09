from elasticsearch_dsl import AsyncSearch, AsyncDocument


class ElasticsearchClient:

    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def get_doc(index_name: str, id_: str | None = None):

        class doc(AsyncDocument):
            id = id_

            class Index:
                name = index_name

        document = doc(_id=id_)
        return document

    async def close(self):
        await self.connection.close()

    async def create(self, index: str, body: dict):
        res = await AsyncDocument(**body).save(
            using=self.connection,
            index=index,
        )
        return res

    async def get(self, index: str, filters: dict, limit: int = 100, offset: int = 0):
        if not filters:
            search = AsyncSearch(index=index, using=self.connection)
            search = search.extra(size=limit, from_=offset)
            result = await search.execute()
        elif 'id' in filters:
            doc = self.get_doc(index)
            result = await doc.get(id=filters['id'])
            return result
        else:
            search = AsyncSearch(index=index, using=self.connection)
            search = search.extra(size=limit, from_=offset)
            search = search.filter(**filters)
            result = await search.execute()
        return [{**i._source, "id": i._id} for i in result.hits.hits]

    async def update(self, index: str, id_: str, body: dict):
        doc = self.get_doc(index, id_)
        res = await doc.update(**body)
        return res

    async def delete(self, index: str, id_: str):
        doc = self.get_doc(index, id_)
        res = await doc.delete()
        return res
