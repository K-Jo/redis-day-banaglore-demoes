import time
import random
import threading
from typing import Dict

import redis
import click


FRIDGE_IDS = [1, 2, 3]


FRIDGE_DOOR_STATUS_KEY_TEMPLATE = 'fridge:{fridge_id}:door_open'
FRIDGE_TEMPERATURE_KEY_TEMPLATE = 'fridge:{fridge_id}:temperature'
FRIDGE_BEER_COUNT_KEY_TEMPLATE = 'fridge:{fridge_id}:beer_count'

TEMPERATURE_CHANGE_RATE = 1
INITIAL_TEMPERATURE = 10
TEMPERATURE_LOWER_LIMIT = 10
TEMPERATURE_UPPER_LIMIT = 40

INITIAL_BEER_COUNT = 5


def initialize_fridge_statuses(r: redis.Redis):
    """
    Initializes the door open status, beer count and the temperature for each fridge.
    """
    for fridge_id in FRIDGE_IDS:
        door_status_key = FRIDGE_DOOR_STATUS_KEY_TEMPLATE.format(fridge_id=fridge_id)
        temperature_key = FRIDGE_TEMPERATURE_KEY_TEMPLATE.format(fridge_id=fridge_id)
        beer_count_key = FRIDGE_BEER_COUNT_KEY_TEMPLATE.format(fridge_id=fridge_id)
        r.set(door_status_key, 0)
        r.set(temperature_key, INITIAL_TEMPERATURE)
        r.set(beer_count_key, INITIAL_BEER_COUNT)


def update_fridge_temperatures(redis_conn: redis.Redis):
    """
    For each fridge, if the door is open, increases the temperature of the fridge.
    """
    for fridge_id in FRIDGE_IDS:
        door_status_key = FRIDGE_DOOR_STATUS_KEY_TEMPLATE.format(fridge_id=fridge_id)
        temperature_key = FRIDGE_TEMPERATURE_KEY_TEMPLATE.format(fridge_id=fridge_id)
        door_open = bool(int(redis_conn.get(door_status_key)))
        curr_temp = float(redis_conn.get(temperature_key))
        if door_open and curr_temp < TEMPERATURE_UPPER_LIMIT:
            curr_temp += TEMPERATURE_CHANGE_RATE
            redis_conn.set(temperature_key, curr_temp)
        elif curr_temp > TEMPERATURE_LOWER_LIMIT:
            curr_temp -= TEMPERATURE_CHANGE_RATE
            redis_conn.set(temperature_key, curr_temp)


def main_loop(r: redis.Redis):
    """
    Runs the main loop which pushes values to time series.
    """
    while True:
        update_fridge_temperatures(r)
        for fridge_id in FRIDGE_IDS:
            temperature_key = FRIDGE_TEMPERATURE_KEY_TEMPLATE.format(fridge_id=fridge_id)
            beer_count_key = FRIDGE_BEER_COUNT_KEY_TEMPLATE.format(fridge_id=fridge_id)
            curr_temp = r.get(temperature_key)
            curr_beer_count = r.get(beer_count_key)
            ts = int(time.time())
            r.execute_command('TS.ADD', f'temperature:{fridge_id}', ts, curr_temp, 'LABELS', 'fridge_id', fridge_id, '__name__', 'temperature', '__class__', 'fridge')
            r.execute_command('TS.ADD', f'beer_count:{fridge_id}', ts, curr_beer_count, 'LABELS', 'fridge_id', fridge_id, '__name__', 'beer_count', '__class__', 'fridge')
        time.sleep(1)


def get_fridge_door_open_status(redis_conn: redis.Redis) -> Dict[int, bool]:
    result = {}
    for fridge_id in FRIDGE_IDS:
        door_status_key = FRIDGE_DOOR_STATUS_KEY_TEMPLATE.format(fridge_id=fridge_id)
        door_open = bool(int(redis_conn.get(door_status_key)))
        result[fridge_id] = door_open
    return result


def get_fridge_beer_counts(redis_conn: redis.Redis) -> Dict[int, int]:
    result = {}
    for fridge_id in FRIDGE_IDS:
        beer_count_key = FRIDGE_BEER_COUNT_KEY_TEMPLATE.format(fridge_id=fridge_id)
        beer_count = int(redis_conn.get(beer_count_key))
        result[fridge_id] = beer_count
    return result


def print_fridge_status(fridge_door_status: Dict[int, bool], fridge_beer_counts: Dict[int, int]):
    for fridge_id in FRIDGE_IDS:
        door_status = fridge_door_status[fridge_id]
        beer_count = fridge_beer_counts[fridge_id]
        print(f"Fridge {fridge_id}:\t{'[OPEN]  ' if door_status else '[CLOSED]'}\t{beer_count} beers")


def fridge_controller(host: str, port: int):
    redis_conn = redis.Redis(host=host, port=port)
    while True:
        # Print current state
        fridge_door_status = get_fridge_door_open_status(redis_conn)
        fridge_beer_counts = get_fridge_beer_counts(redis_conn)
        print('\n')
        print_fridge_status(fridge_door_status, fridge_beer_counts)

        # Get input: fridge ID and action
        which_fridge = input("Which fridge?: ")
        try:
            which_fridge = int(which_fridge)
        except ValueError:
            print(f"'{which_fridge}' is not a valid fridge ID. Try again")
            continue
        if which_fridge not in FRIDGE_IDS:
            print(f"Fridge '{which_fridge}' does not exist, choices are {','.join(FRIDGE_IDS)}. Try again.")
            continue
        action = input("Enter `o` to open, `c` to close, 't' to take a beer: ").lower()
        if action not in ('o', 'c', 't'):
            print(f"Invalid action '{action}'. Try again.")
            continue

        # Perform action
        if action in ('o', 'c'):
            open_door = True if action == 'o' else False
            if fridge_door_status[which_fridge] and open_door:
                print("Door is already open, try again")
                continue
            elif not fridge_door_status[which_fridge] and not open_door:
                print("Door is already closed, try again")
                continue
            door_status_key = FRIDGE_DOOR_STATUS_KEY_TEMPLATE.format(fridge_id=which_fridge)
            redis_conn.set(door_status_key, 1 if open_door else 0)
            print(f"Fridge {which_fridge} door {'opened' if open_door else 'closed'}")
        elif action == 't':
            if not fridge_door_status[which_fridge]:
                print(f"Fridge {which_fridge} is closed. Open if first.")
                continue
            beer_count_key = FRIDGE_BEER_COUNT_KEY_TEMPLATE.format(fridge_id=which_fridge)
            curr_beer_count = int(redis_conn.get(beer_count_key))
            if curr_beer_count == 0:
                print("All out of beers :(")
                continue
            redis_conn.decr(beer_count_key)
            print(f"Beer taken. Drink resposibly :)")
        else:
            # Should never be reached since action is already validated before this condition chain.
            print(f"Invalid action '{action}'. Try again.")


@click.command()
@click.option('--host', default="localhost", help='redis host.')
@click.option('--port', type=click.INT, default=6379, help='redis port.')
def main(host, port):
    r = redis.Redis(host=host, port=port)
    initialize_fridge_statuses(r)
    fridge_controller_thread = threading.Thread(target=fridge_controller, args=(host, port))
    fridge_controller_thread.start()
    main_loop(r)
    # Main loop continues until stopped by a KeyboardInterrupt (ctrl-C).
    # The other thread also continues, so KeyboardInterrupt (ctrl-C) has to be raised twice to exit the process


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
