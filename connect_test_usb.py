mport asyncio
from mavsdk import System

async def run():
  drone = System()
  await drone.connect(system_address="serial:///dev/ttyACM0:115200")
  status_text_task = asyncio.ensure_future(print_status_text(drone))
  print("Waiting for drone to connect...")
  async for state in drone.core.connection_state():
    if state.is_connected:
      print(f"-- Connected to drone!")
      break
  print("-- Arming")
  await drone.action.arm()
  while True:
        print("Staying connected, press Ctrl-C to exit")
        await asyncio.sleep(1)
async def print_status_text(drone):
  try:
      async for status_text in drone.telemetry.status_text():
  except asyncio.CancelledError:
      return

if __name__ == "__main__":
  asyncio.run(run())

