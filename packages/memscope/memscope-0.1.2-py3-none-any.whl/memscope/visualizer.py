import matplotlib.pyplot as plt

def plot_memory_timeline(events):
    steps = [e["step"] for e in events]
    allocated = []
    total = 0
    for e in events:
        total += e["allocated"] - e["freed"]
        allocated.append(total)

    plt.figure(figsize=(8, 4))
    plt.plot(steps, allocated, marker='o')
    plt.title("Heap Allocation Over Time")
    plt.xlabel("Step")
    plt.ylabel("Total Bytes Allocated")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_memory_bars(events):
    steps = [e["step"] for e in events]
    deltas = [e["allocated"] - e["freed"] for e in events]
    colors = ['green' if d >= 0 else 'red' for d in deltas]

    plt.figure(figsize=(8, 4))
    plt.bar(steps, deltas, color=colors)
    plt.title("Heap Memory Operations")
    plt.xlabel("Step")
    plt.ylabel("Δ Bytes")
    plt.axhline(0, color='black', linewidth=0.5)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
