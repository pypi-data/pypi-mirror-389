from memscope.visualizer import plot_memory_timeline

events = [
    {"step": 1, "allocated": 128, "freed": 0},
    {"step": 2, "allocated": 256, "freed": 0},
    {"step": 3, "allocated": 0,   "freed": 128},
    {"step": 4, "allocated": 0,   "freed": 256},
]

plot_memory_timeline(events)
