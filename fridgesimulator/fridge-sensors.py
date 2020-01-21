import time
import random
import threading
from typing import Dict

import redis
import click


FRIDGE_IDS = [1, 2, 3]


FRIDGE_DOOR_STATUS_KEY_TEMPLATE = 'fridge:{fridge_id}:door_open'
FRIDGE_TEMPERATURE_KEY_TEMPLATE = 'fridge:{fridge_id}:temperature'

TEMPERATURE_CHANGE_RATE = 1
INITIAL_TEMPERATURE = 10
TEMPERATURE_LOWER_LIMIT = 10
TEMPERATURE_UPPER_LIMIT = 40


def initialize_fridge_statuses(r: redis.Redis):
    """
    Initializes the door open status and the temperature for each fridge.
    """
    for fridge_id in FRIDGE_IDS:
        door_status_key = FRIDGE_DOOR_STATUS_KEY_TEMPLATE.format(fridge_id=fridge_id)
        temperature_key = FRIDGE_TEMPERATURE_KEY_TEMPLATE.format(fridge_id=fridge_id)
        r.set(door_status_key, 0)
        r.set(temperature_key, INITIAL_TEMPERATURE)


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
            curr_temp = r.get(temperature_key)
            ts = int(time.time())
            # print("fridge", fridge_id, 'temperature', curr_temp)
            r.execute_command('TS.ADD', f'temperature:{fridge_id}', ts, curr_temp, 'LABELS', 'fridge_id', fridge_id)
        time.sleep(1)


def get_fridge_door_open_status(redis_conn: redis.Redis) -> Dict[int, bool]:
    result = {}
    for fridge_id in FRIDGE_IDS:
        door_status_key = FRIDGE_DOOR_STATUS_KEY_TEMPLATE.format(fridge_id=fridge_id)
        door_open = bool(int(redis_conn.get(door_status_key)))
        result[fridge_id] = door_open
    return result

def print_fridge_door_open_status(fridge_door_status: Dict[int, bool]):
    for fridge_id, door_status in fridge_door_status.items():
        print(f"Fridge {fridge_id}: {'OPEN' if door_status else 'CLOSED'}")

def fridge_controller(host: str, port: int):
    redis_conn = redis.Redis(host=host, port=port)
    while True:
        fridge_door_status = get_fridge_door_open_status(redis_conn)
        print_fridge_door_open_status(fridge_door_status)
        print()
        open_or_close = input("Enter `o` to open, `c` to close: ").lower()
        if open_or_close not in ('o', 'c'):
            print("Wrong input, try again")
            continue
        open_door = True if open_or_close == 'o' else False
        which_fridge = input("Which fridge?: ")
        try:
            which_fridge = int(which_fridge)
        except ValueError:
            print(f"'{which_fridge}' is not a valid fridge ID, choices are {','.join(FRIDGE_IDS)}. Try again")
            continue
        if which_fridge not in FRIDGE_IDS:
            print(f"Fridge '{which_fridge}' does not exist, try again.")
            continue
        elif fridge_door_status[which_fridge] and open_door:
            print("Door is already open, try again")
            continue
        elif not fridge_door_status[which_fridge] and not open_door:
            print("Door is already closed, try again")
            continue
        door_status_key = FRIDGE_DOOR_STATUS_KEY_TEMPLATE.format(fridge_id=which_fridge)
        redis_conn.set(door_status_key, 1 if open_door else 0)
        print(f"Fridge {which_fridge} door {'opened' if open_door else 'closed'} successfully!\n")
        



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
    main()
