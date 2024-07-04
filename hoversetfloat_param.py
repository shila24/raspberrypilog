import asyncio
from mavsdk import System
from logger_drone import logger_info, logger_debug

ALTITUDE = 0.3
LAND_ALT = 1.0
mode = None

async def run():
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
  await drone.param.set_float_param("MIS_TAKEOFF_ALT", ALTITUDE)
  await drone.action.takeoff()
  await drone.action.hold()
  await asyncio.sleep(10)
  logger_info.info("-- Landing")
  await drone.action.land()
  print_acceleration_frd.cancel()
  

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
        mode = flight_mode

if __name__ == "__main__":
  loop = asyncio.get_event_loop()
  loop.run_until_complete(run())
