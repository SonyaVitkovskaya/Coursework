
from neo4j import AsyncGraphDatabase
import asyncio

class Genre_Selection():
    def __init__(self, uri, user, password):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.tags = []
        self.categories = []
        self.genres1 =[] 
        self.cat = {}
        self.genres = {}
        self.max = ''

    #запрос в neo4j
    async def db_request(self, string):
        session = self.driver.session(database='neo4j')
        try:
            result = await session.run(string)
            return [record async for record in result]
        except asyncio.CancelledError:
            session.cancel()
            raise
        finally:
            await session.close()

    async def take_genres_and_categories(self):
        response = await self.db_request("MATCH (a:Class{name:'concept_genre'})<-[r:nrel_belong_to]-(il:Class) RETURN il.name")
        for record in response:
            self.genres[record.value()] = []

        response = await self.db_request("MATCH (a:Class{name:'concept_category'})<-[r:nrel_belong_to]-(il:Node) RETURN il.name")
        for record in response:
            self.cat[record.value()] = 0

        response = await self.db_request("MATCH (a:Class{name:'concept_genre'})<-[r:nrel_belong_to]-(il:Class)-[p:nrel_characterized_by]->(g:Node) RETURN il.name, p.factor, g.name")
        for record in response:
            note = record.values()
            self.genres[note[0]].append((note[2], note[1]))

    #поиск тегов изображения
    async def take_tags(self):
        await self.take_genres_and_categories()
        response = await self.db_request("MATCH (a:Class{name:'concept_request'})-[r:context]->(il:Node)-[:nrel_tag]->(tag:Node) RETURN tag.name")
        for record in response:
            self.tags.append(record.value())

    #чтение из файла набора
    async def take_file_rows(self, filename):
        with open(filename) as file:
            return [row.strip() for row in file]
        
    #определение в файле
    async def take_tag_cat(self, filename, category, tag):
        category_tags = await self.take_file_rows(filename)
        for element in category_tags:
            if tag in element or element in tag: 
                self.cat[category] +=1
                break

    #распределение тегов по категориям
    async def category(self):
        for tag in self.tags:
            for category in self.cat:
                await self.take_tag_cat(f"{category}.txt", category, tag)
    
    async def count_max(self):
        max = 0
        for genre in self.genres:
            check_max = 0
            for category in self.genres[genre]:
                check_max += self.cat[category[0]]*category[1]
                if check_max > max:
                    max=check_max
                    self.max = genre

    async def get_genre(self):
        await self.db_request(f"MATCH (p:Class{{name: 'concept_request'}})-[:context]->(a:Node), (g:Class{{name: '{self.max}'}}) \n CREATE(a)-[:nrel_genre]->(g)")

        
async def take_g():
    i = Genre_Selection(uri="bolt://localhost:7687", user = "neo4j",password="Qw8pPruC430167")
    await i.take_tags()
    #await i.category()
    #await i.count_max()
    #await i.get_genre()

asyncio.run(take_g())
