# NEEDS UPDATING

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
Open a second terminal to connect to redis and explore the dataset:
```
$ redis-cli
```

## RedisInsight
http://localhost:8001/

## TimeSeries Demo

1. `pip install click redis`
1. `python3 ./fridgesimulator/fridge-sensors.py --port 6382`
1. In RedisInsight, go to the "redistimeseries" db and switch to RedisTimeSeries tool
1. Run query: `TS.MRANGE - + FILTER __class__=fridge`
1. Set Y-axis min to 0 and max to 40
1. Toggle on auto-update (top-right side of query card)
1. Open a fridge, take some beers and then close it
