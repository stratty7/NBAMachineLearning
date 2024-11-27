def american_to_decimal(american_odds):
    """
    Converts American odds to decimal odds (European odds).
    """
    if american_odds >= 100:
        decimal_odds = (american_odds / 100)
    else:
        decimal_odds = (100 / abs(american_odds))
    return round(decimal_odds, 2)

def calculate_kelly_criterion(odds, model_prob, bankroll):
    """
    Calculates the fraction of the bankroll to be wagered on each bet
    """
    p = model_prob
    q = 1-model_prob
    b = odds - 1
    (p*b - q) / b

    bankroll_fraction = (p*b - q) / b
    bankroll_amount = round(bankroll*bankroll_fraction, 2)
    return bankroll_amount if bankroll_amount > 0 else 0