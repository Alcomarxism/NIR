import agents

class Squad():
    def __init__(self, sim,recoons_start_pos,squad_name):
        self.squad_name = squad_name
        self.sim = sim
        self.map = [['?' for _ in range(len(sim.map))] for _ in range(len(sim.map))]
        self.agents={agents.AgentRecoon(recoons_start_pos[i],squad_name+" Recoon"+str(i),self,self.sim) for i in range(len(recoons_start_pos))}
        self.orders={squad_name+" Recoon"+str(i): "Нет приказа" for i in range(len(recoons_start_pos))}
        self.reports={squad_name+" Recoon"+str(i): "Нет отчета" for i in range(len(recoons_start_pos))}
        self.commander=agents.AgentComander(self)
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
