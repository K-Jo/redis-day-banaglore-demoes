import csv
import redis
import random
import string
import os

def random_string(length=5):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def clean_string(s):
    s = s.replace("\"", "")
    s = s.replace("\\", "")
    s = s.encode('ascii', 'ignore').decode('ascii')


REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

class Node:
    def __init__(self, label, props):
        self.alias = random_string()
        self.label = label
        self.props = props
        self.raw_node = f'({self.alias}:{self.label}{self.props})'

def generate_edge_query(s_type, s_name, s_val, t, d_type, d_name, d_val):
    return f'MATCH(s:{s_type}{{{s_name}:{s_val}}}),(d:{d_type}{{{d_name}:{d_val}}}) CREATE(s)-[:{t}]->(d)'

class Edge:
    def __init__(self, src, dest, relationship, props=None):
        self.alias = random_string()
        self.src = src
        self.dest = dest
        self.relationship = relationship
        self.props = props if props else ''
        self.raw_edge = f'({self.src.alias})-[:{self.relationship}{self.props}]->({self.dest.alias})'

class Graph:
    def __init__(self, graph_name):
        self.graph_name = graph_name
        self.nodes = []
        self.edges = []
        self.lazy_edges = []

    def add_node(self, node):
        self.nodes.append(node)

    def add_edge(self, edge):
        self.edges.append(edge)

    def add_edge_lazy(self, s_type, s_name, s_val, t, d_type, d_name, d_val):
        self.lazy_edges.append(f'MATCH(s:{s_type}{{{s_name}:{s_val}}}),(d:{d_type}{{{d_name}:{d_val}}}) CREATE(s)-[:{t}]->(d)')

    def commit(self):
        for node in self.nodes:
            redis_conn.execute_command('GRAPH.QUERY', *[self.graph_name, 'CREATE ' + node.raw_node])
        for q in self.lazy_edges:
            redis_conn.execute_command('GRAPH.QUERY', *[self.graph_name, q])


beer_redis_graph = Graph('rg:beer')

def import_beer():
    redis_conn.execute_command('DEL rg:beer')

    categories = {}

    with open('data/categories.csv') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        label = 'Category'

        for row in reader:
            id = row[0]
            cat_name = row[1]
            last_mod = row[2]

            props = f'{{cid: {id}, name:"{cat_name}",last_mod:"{last_mod}"}}'
            node = Node(label, props)
            categories[id] = node
            beer_redis_graph.add_node(node)

    styles = {}

    with open('data/styles.csv') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        label = 'Style'
        
        for row in reader:
            id = row[0]
            cat_id = row[1]
            style_name = row[2]
            last_mod = row[3]
            props = f'{{sid: {id}, name:"{style_name}",last_mod:"{last_mod}"}}'
            node = Node(label, props)
            styles[id] = node
            beer_redis_graph.add_node(node)

            if cat_id in categories.keys():
                dest_label = 'Category'
                relationship = 'IS_CATEGORY'
                beer_redis_graph.add_edge_lazy(label, 'sid', id, relationship, dest_label, 'cid', cat_id)

    breweries = {}

    with open('data/breweries.csv') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        label = 'Brewery'

        for row in reader:
            id = row[0]
            name = row[1]
            address1 = row[2]
            address2 = row[3]
            city = row[4]
            state = row[5]
            code = row[6]
            country = row[7]
            phone = row[8]
            website = row[9]
            filepath = row[10]
            description = None
            props = f'{{bwid:{id},name:"{name}",address1:"{address1}",address2:"{address2}",city:"{city}",state:"{state}",code:"{code}",country:"{country}",phone:"{phone}",website:"{website}",filepath:"{filepath}", description:"{description}"}}'
            node = Node(label, props)
            breweries[id] = node
            beer_redis_graph.add_node(node)

    breweries_geocode = {}

    with open('data/breweries_geocode.csv') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        label = 'Geocode'

        for row in reader:
            id = row[0]
            brew_id = row[1]
            latitude = row[2]
            longitude = row[3]
            accuracy = row[4]
            props = f'{{gid:{id},latitude:{latitude},longitude:{longitude},accuracy:"{accuracy}"}}'
            node = Node(label, props)
            breweries_geocode[id] = node
            beer_redis_graph.add_node(node)

            if brew_id in breweries.keys():
                dest_label = 'Brewery'
                relationship = 'LOCATED_IN'
                beer_redis_graph.add_edge_lazy(label, 'gid', id, relationship, dest_label, 'bwid', brew_id)

    beers = {}

    with open('data/beers.csv') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        label = 'Beer'
        
        for row in reader:
            id = row[0]
            brew_id = row[1]
            name = row[2].replace("\"", "")
            name = name.replace("\\", "")
            cat_id = row[3]
            style_id = row[4]
            abv = row[5]
            ibu = row[6]
            srm = row[7]
            upc = row[8]
            filepath = row[9]
            description = None
            last_mod = None

            props = f'{{bid:{id}, name:"{name}",abv:"{abv}",ibu:"{ibu}",srm:"{srm}",upc:"{upc}",filepath:"{filepath}",description:"{description}"}}'

            node = Node(label, props)
            breweries[id] = node
            beer_redis_graph.add_node(node)

            if brew_id in breweries.keys():
                dest_label = 'Brewery'
                relationship = 'BREWED_BY'
                beer_redis_graph.add_edge_lazy(label, 'bid', id, relationship, dest_label, 'bwid', brew_id)

            if cat_id in categories.keys():
                dest_label = 'Category'
                relationship = 'IN_CATEGORY'
                beer_redis_graph.add_edge_lazy(label, 'bid', id, relationship, dest_label, 'cid', cat_id)

            if style_id in styles.keys():
                dest_label = 'Style'
                relationship = 'IS_STYLE'
                beer_redis_graph.add_edge_lazy(label, 'bid', id, relationship, dest_label, 'sid', style_id)


    persons = {}

    with open('data/person.csv') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        label = 'Person'

        for row in reader:
            id = row[0]
            name = row[1]
            props = f'{{pid:{id},name:"{name}"}}'
            node = Node(label, props)
            persons[id] = node
            beer_redis_graph.add_node(node)

    with open('data/person_likes_beer.csv') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        for row in reader:
            pid = row[0]
            bid = row[1]
            beer_redis_graph.add_edge_lazy('Person', 'pid', pid, 'LIKES', 'Beer', 'bid', bid)


    beer_redis_graph.commit()

import_beer()
