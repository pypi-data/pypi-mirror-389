from memscope import analyze_source, simulate_malloc, simulate_free, heap_view

# ניתוח קוד C
result = analyze_source(r"C:\Users\A\source\repos\memscope\examples\sample.c")
print("Analysis:", result)

# הדמיית הקצאות
simulate_malloc([
    {"ptr": "a", "size": 128},
    {"ptr": "b", "size": 64}
])
simulate_free("a")

# צפייה ב־heap
print("Heap view:", heap_view())
