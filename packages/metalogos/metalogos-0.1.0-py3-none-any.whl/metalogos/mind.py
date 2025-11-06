class BeliefAgent:
    def __init__(self, name, belief_strength=0.5):
        self.name = name
        self.belief_strength = belief_strength
        self.memory = []

    def observe(self, event, weight=0.5):
        """Observe an event and store its influence."""
        self.memory.append((event, weight))
        self.belief_strength *= (1 - weight)

    def reflect(self):
        """Reflect upon all observations."""
        reflection = sum(w for _, w in self.memory)
        print(f"{self.name} reflected on {len(self.memory)} events. Total weight: {reflection:.2f}")
        print(f"Current belief strength: {self.belief_strength:.2f}")
