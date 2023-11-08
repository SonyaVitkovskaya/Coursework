from neo4j import AsyncGraphDatabase
import asyncio

class Genre_Selection():
    def __init__(self, uri, user, password):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.tags = []
        self.cat = {"clothes":0, 'd_anim':0, "flowers":0, 'food':0, 'furniture':0, 'harvest':0, 'household_utensils':0,
                     'people':0, 'prir':0, 'street':0, 'tableware':0, 'w_anim':0}
        self.genres = {"concept_portrait":['people',"clothes"],
                        "concept_household":['people', "clothes", 'd_anim', 'food', 'furniture', 'household_utensils', 'prir', 'tableware'],
                          "concept_still_life":["flowers",'furniture','harvest','tableware'],
                            "concept_scenery":[ "flowers", 'prir'], 
                            "concept_town_scenery":['people','d_anim', 'street'],
                              "concept_animalistic":['d_anim', 'household_utensils', 'prir', 'street', 'w_anim']}
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

    #поиск тегов изображения
    async def take_tags(self):
        response = await self.db_request("MATCH(a:Class{name:'concept_request'})-[r:context]->(il:Node)-[:nrel_tag]->(tag:Node) RETURN tag.name")
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
                check_max += self.cat[category]
                if check_max > max:
                    max=check_max
                    self.max = genre

    async def get_genre(self):
        await self.db_request(f"MATCH (p:Class{{name: 'concept_request'}})-[:context]->(a:Node), (g:Class{{name: '{self.max}'}}) \n CREATE(a)-[:nrel_genre]->(g)")

        
async def checking_base():
    i = Genre_Selection(uri="bolt://localhost:7687", user = "neo4j",password="Qw8pPruC430167")
    await i.take_tags()
    await i.category()
    await i.count_max()
    await i.get_genre()

asyncio.run(checking_base())
