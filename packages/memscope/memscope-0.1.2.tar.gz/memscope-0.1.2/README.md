# memscope

🔍 Analyze and visualize memory allocation and release operations in C/C++ code.

## 🚀 Features

- Detects `malloc`, `calloc`, `realloc`, `new`, `delete`, `free`
- Counts allocation vs. deallocation operations
- Detects potential memory leaks
- Visualizes heap behavior over time using Matplotlib

## 📦 Installation

bash
pip install memscope


Or from source:
git clone https://github.com/MiriKanner/memscope
cd memscope
pip install -e

## 🧠 Quick Start
Analyze C/C++ Source Code

from memscope import analyze_source

result = analyze_source("examples/sample.c")
print(result)

example output:

{
    "allocs": 2,
    "frees": 1,
    "unfreed_allocations": 1,
    "lines": {
        "alloc": [4, 7],
        "free": [9]
    }
}

Visualize Memory Operations

from memscope.visualizer import plot_memory_timeline, plot_memory_bars

events = [
    {"step": 1, "allocated": 128, "freed": 0},
    {"step": 2, "allocated": 256, "freed": 64},
    {"step": 3, "allocated": 0,   "freed": 320},
]

plot_memory_timeline(events)
plot_memory_bars(events)


## 🧩 API Reference


analyze_source(filepath: str) -> dict

Analyze a C/C++ source file and detect allocation/deallocation operations.

Parameters

---filepath: path to .c or .cpp file.

Returns:
{
    "allocs": int,
    "frees": int,
    "unfreed_allocations": int,
    "lines": {"alloc": list[int], "free": list[int]}
}


plot_memory_timeline(events: list[dict])

Plots total heap size over time.

plot_memory_timeline([
    {"step": 1, "allocated": 128, "freed": 0},
    {"step": 2, "allocated": 0, "freed": 128},
])

plot_memory_bars(events: list[dict])

Plots allocation (green) and free (red) deltas.

plot_memory_bars([
    {"step": 1, "allocated": 200, "freed": 0},
    {"step": 2, "allocated": 0, "freed": 100},
])



