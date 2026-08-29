import visualization
import asyncio
import simulation

sim=simulation.Simulation()
vis=visualization.Visualizator()


async def main():
    asyncio.create_task(sim.run_async_simulation())
    await vis.run_async_visualization(sim)

if __name__ == "__main__":
    asyncio.run(main())