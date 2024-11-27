def expected_value(Pwin, odds, bankroll):
    # print(Pwin) # 0.60404
    # print(odds) # 1.23
    Ploss = 1 - Pwin # 0.39596
    Mwin = bankroll * odds - bankroll
    return round((Pwin * Mwin) - (Ploss * bankroll), 2)

