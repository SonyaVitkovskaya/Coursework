from neo4j import GraphDatabase
import asyncio

uri="bolt://localhost:7687"
user = "neo4j"
password=""

driver = GraphDatabase.driver(uri, auth=(user, password))
tags =[]

a = 'MATCH (b:Class{name: "node_class"}) CREATE (n:Class{name: "concept_category"})-[:nrel_belong_to]->(b)'

def db_request(string):
    session = driver.session(database='neo4j')
    try:
        result = session.run(string)
        return [record for record in result]
    except Exception:
        session.cancel()
        raise
    finally:
        session.close()

def take_tags():
    categories = ["clothes", 'domestic animals', "flowers", 'food', 'furniture', 'harvest', 'household utensils',
                     'people', 'nature', 'street', 'tableware', 'wild anim']
    
    req1 = 'MATCH (b:Class{name: "concept_category"})  '
    for category_id in range(len(categories)):
        req1 += f"CREATE (n{category_id}:Node {{name:'{categories[category_id]}'}})-[:nrel_belong_to]->(b) "
    db_request(req1)

    genres = {"concept_portrait":[('people', 0.3), ("clothes", 0.1), ('furniture', 0.1)],
                "concept_household":[('people', 0.2), ("clothes",0.2), ('domestic animals', 0.2), ('food', 0.1), ('furniture', 0.2),
                                      ('household utensils', 0.3), ('nature', 0.1), ('harvest', 0.1)],
                    "concept_still_life":[("flowers", 0.3 ),('furniture', 0.1) ,('harvest',0.3),('tableware', 0.3)],
                        "concept_scenery":[ ("flowers", 0.2), ('nature', 0.3)], 
                            "concept_town_scenery":[('people', 0.1),('domestic animals', 0.1), ('street', 0.3)],
                                "concept_animalistic":[('domestic animals', 0.3), ('household utensils', 0.1),  ('nature', 0.1), ('wild anim', 0.3)]}
    
    for genre in genres:
       if genre != "concept_portrait": db_request(f'MATCH (a:Class {{name:"node_class"}})  CREATE(l:Class {{name:"{genre}"}})-[:nrel_belong_to]->(a)')

    for genre in genres:
        for categ in genres[genre]:
            req = f"MATCH (b:Class {{name:'{genre}'}})  MATCH(a:Node {{name:'{categ[0]}'}}) CREATE(a)<-[:nrel_characterized_by{{factor: {categ[1]} }}]-(b)  "
            db_request(req)
    
    req2 = 'MATCH (f:Class {name:"node_class"})  CREATE (l:Class {name: "concept_genre"})-[:nrel_belong_to]->(f)     '
    genres2 = list(genres.keys())
    db_request(req2)

    for genre_id in range(len(genres2)):
        req3 = f' MATCH (l:Class{{name: "concept_genre"}}) MATCH (a:Class {{name: "{genres2[genre_id]}"}}) CREATE (a)-[:nrel_belong_to]->(l)     '
        db_request(req3)


db_request(a)
take_tags()
