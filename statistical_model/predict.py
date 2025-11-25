def predict_taxi_time(path_list, ident_lengths, avg_speed):
    total_distance = 0
    
    for ident in path_list:
        # Try exact match first
        if ident in ident_lengths:
            total_distance += ident_lengths[ident]
            continue

        # Fallback: strip trailing digits (e.g., 'F5' -> 'F') and try again
        alpha = ''.join([c for c in ident if c.isalpha()])
        if alpha and alpha in ident_lengths:
            total_distance += ident_lengths[alpha]
            continue

        # No match found
        available = ', '.join(sorted(list(ident_lengths.keys())[:20]))
        raise ValueError(
            f"Taxiway '{ident}' not found in graph. "
            f"Tried exact match and alpha-prefix '{alpha}'. Available idents (sample): {available}"
        )

    time_sec = total_distance / avg_speed
    return total_distance, time_sec
