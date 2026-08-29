import agents
import enviroment

class Simulation():
    def __init__(self):
        self.env = enviroment.Enviroment()
        self.agent=agents.Agent()
        self.target_str = f"{self.env.target_pos[0]},{self.env.target_pos[1]}"

    async def step(self,step_num):
        visibility = self.env.get_fog_view(radius=1)
        print(f"\n[Шаг {step_num}]")
        action= await self.agent.make_desigion(self.env.agent_pos,visibility,self.target_str)
        success, feedback = self.env.step(action)
        self.agent.get_feedback(feedback)        
    
    async def run_async_simulation(self):
        for step_num in range(1, 80):  
                await self.step(step_num)
