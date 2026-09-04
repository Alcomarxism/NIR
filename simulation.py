import squad
import enviroment

class Simulation():
    def __init__(self):
        self.env = enviroment.Enviroment()
        self.squad1=squad.Squad(self.env,[(1,1),(1,2),(2,1)])
        self.squad2=squad.Squad(self.env,[(18,18),(17,18),(18,17)])
    async def step(self,step_num):
        print(f"\n[Шаг {step_num}]")
        await self.squad1.step()
        await self.squad2.step()

    async def run_async_simulation(self):
        for step_num in range(1, 80):  
                await self.step(step_num)
