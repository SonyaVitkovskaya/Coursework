import cv2
import neo4j
from neo4j import AsyncGraphDatabase
import asyncio

class CheckingImgDB():
    def __init__(self, uri, user, password):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.user_path = ''
        self.user_hash = ''
        self.min = 20
        self.list_of_pathes = []

    #вычисление хэша через среднее значение пикселей
    async def find_hash(self, file):
        image = cv2.imread(file)
        resized_img = cv2.resize(image, (8,8), interpolation = cv2.INTER_AREA)
        gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
        avg = gray_img.mean()
        ret, bin_img = cv2.threshold(gray_img, avg, 255, 0)
        hash=""
        for x in range(len(bin_img)):
            for y in range(len(bin_img[x])):
                val=bin_img[x,y]
                hash+="1" if val==255  else "0"
        return hash
    
    #сравнение по хэшу
    async def compare(self, path2):
        hash2 = await self.find_hash(path2)
        counter = 0
        for i in range(len(self.user_hash)):
            counter += 1 if self.user_hash[i]!=hash2[i] else 0
        return counter
    
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
    
    #поиск пользовательского изображения
    async def take_user_path(self):
        response = await self.db_request("MATCH (a:Text)<-[r:user_path]-(il:Class{name:'concept_request'}) RETURN a.content")
        self.user_path = response[0].value()
        self.user_hash = await self.find_hash(self.user_path)
    
    #формирования списка-результата сравнения
    async def creating_comparison_lst(self):
        for pic in await self.db_request("MATCH (a:Node)-[r:nrel_belong_to]->(il:Class{name:'illustration'}) RETURN a.name"):
            for path in await self.db_request(f"MATCH (a:Text)<-[r:rrel_example]->(pic:Node{{name:'{pic.value()}'}}) RETURN a.content"):
                check_min = await self.compare(path.value())
                if check_min < self.min: self.min = check_min
                self.list_of_pathes.append((check_min, pic.value()))
        return self.list_of_pathes
    
    #поиск ближайшего по схожести
    async def find_closest(self):
        closest = ''
        for path in self.list_of_pathes:
            if path[0] == self.min:
                close = await self.db_request(f"MATCH (a:Node{{name:'{path[1]}'}})-[r:rrel_key_element]->(il:Node) RETURN il.name")
                closest = close[0].value()
                break
        if closest:
            await self.db_request(f"MATCH (p:Class{{name: 'concept_request'}}), (a:Node{{name:'{closest}'}}) \n CREATE(p)-[:context]->(a)")
        else: print("не нашел")

async def checking_base():
    i = CheckingImgDB(uri="bolt://localhost:7687", user = "neo4j",password="Qw8pPruC430167")
    await i.take_user_path()
    await i.creating_comparison_lst()
    await i.find_closest()

asyncio.run(checking_base())