import csv
import matplotlib.pyplot as plt

class MetricsCollector:
    def __init__(self, squad_name,start_alive_agents):
        self.squad_name = squad_name
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.total_llm_calls = 0
        self.enemies_killed = 0
        self.alive_agents = start_alive_agents
        self.true_move = 0
        self.false_move = 0
        self.true_shoot = 0
        self.false_shoot = 0

    def record_tokens(self, info):
        prompt_tokens = info.get("prompt_eval_count", 0)
        completion_tokens = info.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens 
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total_tokens
        self.total_llm_calls += 1

    def get_metrics(self) -> dict:
        return {
            "avg_tokens_per_call": round(self.total_tokens / max(1, self.total_llm_calls), 2),
            "tokens_per_kill": round(self.total_tokens / max(1, self.enemies_killed), 2),
            "alive_agents": self.alive_agents,
            "enemies_killed": self.enemies_killed,
            "total_true_moves": self.true_move,
            "total_false_moves": self.false_move,
            "total_true_shoots": self.true_shoot,
            "total_false_shoots": self.false_shoot,

        }

