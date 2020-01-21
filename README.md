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
