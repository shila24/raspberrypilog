import asyncio
import time
import RPi.GPIO as GPIO
from mavsdk import System
from logger_drone import logger_info, logger_debug

ALTITUDE = 0.3
LAND_ALT = 1.0
mode = None

# GPIO ピンの設定
PIN_LIST = [11, 13]  # 使用するGPIOピンのリスト
RUN_TIME = 5
SLEEP_TIME = 1
LOOP_COUNT = 1

async def control_mosfets(loop_count):
    GPIO.setmode(GPIO.BOARD)
    for pin in PIN_LIST:
        GPIO.setup(pin, GPIO.OUT)
    
    try:
        for _ in range(loop_count):
            for pin in PIN_LIST:
                GPIO.output(pin, GPIO.HIGH)  # MOSFETをONにする
                logger_info.info(f"Turned ON MOSFET on pin {pin}")
                await asyncio.sleep(RUN_TIME)  # 5秒
                GPIO.output(pin, GPIO.LOW)  # MOSFETをOFFにする
                logger_info.info(f"Turned OFF MOSFET on pin {pin}")
                await asyncio.sleep(SLEEP_TIME)  # 1秒
    finally:
        GPIO.cleanup()

async def run():
    # MOSFET制御のためのループ回数
    await control_mosfets(LOOP_COUNT )
    ogger_info.info("-- palacute has already been separated!!")

    drone = System()
    print("Waiting for drone to connect...")
    await drone.connect(system_address="serial:///dev/ttyACM0:115200")
    logger_info.info("Waiting for drone to connect...")
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            logger_info.info("-- Connected to drone!")
            break

    logger_info.info("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logger_info.info("-- Global position estimate OK")
            break
    
    print("waiting for pixhawk to hold")
    print_altitude_task = asyncio.create_task(print_altitude(drone))
    print_flight_mode_task = asyncio.create_task(print_flight_mode(drone))
    arm_takeoff_task = asyncio.create_task(arm_takeoff(drone))
    await print_altitude_task
    await print_flight_mode_task
    await arm_takeoff_task

async def arm_takeoff(drone):
    logger_info.info("-- Arming")
    await drone.action.arm()
    logger_info.info("-- Armed")
    logger_info.info("-- Taking off")
    await drone.action.set_takeoff_altitude(ALTITUDE)
    await drone.action.takeoff()
    await asyncio.sleep(10)
    logger_info.info("-- Landing")
    await drone.action.land()
    logger_info.info("-- Drone has already landed!!!")

async def print_altitude(drone):
    previous_altitude = 0.0
    async for distance in drone.telemetry.distance_sensor():
        altitude_now = distance.current_distance_m
        print("difference : {}".format(altitude_now - previous_altitude))
        if abs(previous_altitude - altitude_now) >= 0.1:
            previous_altitude = altitude_now
            logger_info.info(f"mode:{mode} lidar:{altitude_now}m")
        
        if altitude_now > LAND_ALT:
            print("over {}".format(LAND_ALT))
            await drone.action.land()

async def print_flight_mode(drone):
    """ Prints the flight mode when it changes """
    async for flight_mode in drone.telemetry.flight_mode():
        global mode
        mode = flight_mode

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
