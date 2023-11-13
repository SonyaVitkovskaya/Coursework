from neo4j import AsyncGraphDatabase
import asyncio

class Genre_Selection():
    def __init__(self, uri, user, password):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.tags = []
        self.cat = {"clothes":0, 'd_anim':0, "flowers":0, 'food':0, 'furniture':0, 'harvest':0, 'household_utensils':0,
                     'people':0, 'prir':0, 'street':0, 'tableware':0, 'w_anim':0}
         self.genres = {"concept_portrait":[('people', 0.3), ("clothes", 0.1), ('furniture', 0.1)],
                        "concept_household":[('people', 0.2), ("clothes",0.2), ('d_anim', 0.2), ('food', 0.1), ('furniture', 0.2), ('household_utensils', 0.3), ('prir', 0.1), ('harvest', 0.1)],
                          "concept_still_life":[("flowers", 0.3 ),('furniture', 0.1) ,('harvest',0.3),('tableware', 0.3)],
                            "concept_scenery":[ ("flowers", 0.2), ('prir', 0.3)], 
                            "concept_town_scenery":[('people', 0.1),('d_anim', 0.3 ), ('street', 0.3)],
                              "concept_animalistic":[('d_anim', 0.3), ('household_utensils', 0.1),  ('prir', 0.1), ('w_anim', 0.3)]}
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
                check_max += self.cat[category[0]]*category[1]
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
