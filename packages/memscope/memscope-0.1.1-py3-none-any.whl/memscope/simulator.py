_heap = []

def simulate_malloc(alloc_list):
    global _heap
    for entry in alloc_list:
        _heap.append({
            "ptr": entry["ptr"],
            "size": entry["size"],
            "status": "allocated"
        })
    return _heap

def simulate_free(ptr_name):
    global _heap
    for block in _heap:
        if block["ptr"] == ptr_name and block["status"] == "allocated":
            block["status"] = "freed"
            return True
    return False

def heap_view():
    total_allocated = sum(b["size"] for b in _heap if b["status"] == "allocated")
    total_freed = sum(b["size"] for b in _heap if b["status"] == "freed")

    return {
        "heap": _heap,
        "total_allocated": total_allocated,
        "total_freed": total_freed
    }
