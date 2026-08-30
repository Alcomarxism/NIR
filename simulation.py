import agents
import enviroment

class Simulation():
    def __init__(self):
        self.env = enviroment.Enviroment()
        self.agent=agents.Agent((2,2))
        self.agent2=agents.Agent((17,17))


    async def step(self,step_num):
        print(f"\n[Шаг {step_num}]")
        await self.agent.make_desigion(self.env)    
        await self.agent2.make_desigion(self.env)    

    async def run_async_simulation(self):
        for step_num in range(1, 80):  
                await self.step(step_num)
