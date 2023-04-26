

# load entry points
def get_entries(entry_point_name="aiidalab_qe_configuration"):
    from importlib.metadata import entry_points

    entries = {}
    for entry_point in entry_points().get(entry_point_name, []):
        entries[entry_point.name] = entry_point.load()
        
    return entries

if __name__ == "__main__":
    print(get_entries())