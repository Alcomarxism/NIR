import squad
import metrics
import time

def generate_field():
    field = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    return field
    
class Simulation():
    def __init__(self):
        self.map = generate_field()
        self.squads={
            "RED":squad.Squad(self,"RED", recoons_start_pos=[(1,3),(3,1)], assault_start_pos=[(1,1),(3,3)]),
            "BLUE": squad.Squad(self,"BLUE",recoons_start_pos=[(13,11),(11,13)], assault_start_pos=[(13,13),(11,11)])
        }
        self.metrics={sqname: metrics.MetricsCollector(sqname)for sqname in self.squads}
    
    async def step(self,step_num):
        print(f"\n[Шаг {step_num}]")
        for sq in self.squads:
            start_time = time.time()
            await self.squads[sq].step()
            step_time = time.time() - start_time
            self.metrics[sq].collect_step(step_num, self.squads[sq], self, step_time)
            metrics.plot_squads_comparison(self.metrics, save_path="squads_comparison.png")
    
    async def run_async_simulation(self):
        for step_num in range(1, 80):  
                await self.step(step_num)
