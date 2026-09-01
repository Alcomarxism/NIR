import agents
import enviroment

class Simulation():
    def __init__(self):
        self.env = enviroment.Enviroment()
        self.agents={agents.AgentRecoon((1,1),"Recoon1"),agents.AgentRecoon((1,2),"Recoon2"),agents.AgentRecoon((2,1),"Recoon3")}
        self.comander=agents.AgentComander(self.agents)

    async def step(self,step_num):
        print(f"\n[Шаг {step_num}]")
        await self.comander.make_desigion(self.env)    
        for a in  self.agents:
            await a.make_desigion(self.env,self.comander)    

    async def run_async_simulation(self):
        for step_num in range(1, 80):  
                await self.step(step_num)
