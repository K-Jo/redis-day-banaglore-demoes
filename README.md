# Modules demoes given with RedisInsight during Redis Day Bangalore 2020

Demoes using the https://openbeerdb.com/ dataset.

## Running the Demo
To run the demo:
```
$ git clone https://github.com/K-Jo/redis-day-banaglore-demoes.git
$ cd redis-day-banaglore-demoes
$ docker-compose up
```
If something went wrong, you might need to force docker-compose to rebuild the containers
```
$ docker-compose up --force-recreate --build
```

## RedisInsight
http://localhost:8001/

## RediSearch Demo

1. Search for your favourite beer in the beer index
1. Add an `alias` to the index and query the alias for your favourite beer

## TimeSeries Demo

1. Install python deps
   ```bash
   pip install click redis
   ```
1. Run fridge simulator script:
   ```bash
   python3 ./fridgesimulator/fridge-sensors.py --port 6382
   ```
1. In RedisInsight, go to the "redistimeseries" db and switch to RedisTimeSeries tool
1. Run query: 
   ```
   TS.MRANGE - + FILTER __class__=fridge
   ```
1. Set Y-axis min to `0` and max to `40`
1. Toggle on auto-update (top-right side of query card)
1. Switch to the fridge simulator terminal. Open a fridge, take some beers and then close it

## RedisGraph Demo
1. Create full-text index on brewery name: 
   ```
   CALL db.idx.fulltext.createNodeIndex('Brewery', 'name')
   ```
2. Run
   ```cypher
    CALL db.idx.fulltext.queryNodes('Brewery', '%brew%') yield node
    MATCH (node)<-[:BREWED_BY]-(b)<-[:LIKES]-(:Person {pid:46})
    WITH node, count(b) as count
    RETURN node.name, count ORDER BY count DESC limit 10
   ```
