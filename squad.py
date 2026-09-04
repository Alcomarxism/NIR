import agents

class Squad():
    def __init__(self, enviroment,recoons_start_pos):
        self.env = enviroment
        self.map = [['?' for _ in range(20)] for _ in range(20)]
        self.agents={agents.AgentRecoon(recoons_start_pos[i],"Recoon"+str(i),self) for i in range(len(recoons_start_pos))}
        self.commander=agents.AgentComander(self.agents,self)

    async def step(self):
        await self.commander.make_desigion(self.env)    
        for a in  self.agents:
            await a.make_desigion(self.env)   