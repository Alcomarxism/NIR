import agents

class Squad():
    def __init__(self,model, sim,squad_name,recoons_start_pos,assault_start_pos):
        self.squad_name = squad_name
        self.sim = sim
        self.map = [['?' for _ in range(len(sim.map))] for _ in range(len(sim.map))]
        recoons = {agents.AgentRecoon(model,recoons_start_pos[i],squad_name+" Recoon"+str(i),self,self.sim) for i in range(len(recoons_start_pos))}
        assaults = {agents.AgentAssault(model,assault_start_pos[i],squad_name+" Assault"+str(i),self,self.sim) for i in range(len(assault_start_pos))}
        self.agents= recoons | assaults
        self.orders={ag.name: "Нет приказа" for ag in self.agents}
        self.reports={ag.name: "Нет отчета" for ag in self.agents}
        self.commander=agents.AgentComander(model,self)
        self.logs=[]

    def print_to_logs(self,text):
        print(text)
        self.logs.append(text)

    def get_logs(self):
        logs=[]
        for ag in self.agents:
            logs.append("Имя: "+ag.name)
            logs.append("Позиция: "+str(ag.pos))
            logs.append("Приказ: "+self.orders[ag.name])
            logs.append("Отчет: "+self.reports[ag.name])
            logs.append("")
        logs+=self.logs
        return logs

    def kill_agent(self,name):
        self.reports[name]="Убит"# в "+str(self.agents[name].pos)
        for ag in self.agents:
            if ag.name==name:
                self.agents.remove(ag)
                break
        #self.orders.pop(name)
    
    async def step(self):
        self.logs=[]
        await self.commander.make_desigion()    
        for a in  self.agents:
            await a.make_desigion()   
