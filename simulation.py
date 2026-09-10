import squad
import enviroment

class Simulation():
    def __init__(self):
        self.env = enviroment.Enviroment()
        self.squads={"RED":squad.Squad(self,self.env,[(1,1),(1,2),(2,1)],"RED"),"BLUE": squad.Squad(self,self.env,[(5,5),(6,5),(5,6)],"BLUE")}

    async def step(self,step_num):
        print(f"\n[Шаг {step_num}]")
        for sq in self.squads:
            await self.squads[sq].step()

    async def run_async_simulation(self):
        for step_num in range(1, 80):  
                await self.step(step_num)
