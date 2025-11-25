def compute_ident_lengths(G):
    ident_lengths = {}

    for u, v, data in G.edges(data=True):
        ident = data.get("Ident")
        dist = data.get("distance", 0)

        if ident not in ident_lengths:
            ident_lengths[ident] = 0
        ident_lengths[ident] += dist

    return ident_lengths
