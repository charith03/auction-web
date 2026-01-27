from .ppi_calculator import calculate_ppi

def evaluate_team(playing_xi_list):
    """
    Evaluates a Playing XI (List of Player objects).
    Returns a dictionary with 'score', 'details' (hidden logic).
    """
    
    total_ppi = 0
    
    # Composition Counters
    role_counts = {
        "BATSMAN": 0,
        "BOWLER": 0,
        "ALL ROUNDER": 0,
        "WICKET KEEPER": 0
    }
    
    for player in playing_xi_list:
        # Calculate individual PPI
        p_ppi = calculate_ppi(player)
        total_ppi += p_ppi
        
        # Count Roles
        role = player.role.upper()
        if "WICKET KEEPER" in role or "WK" in role:
            role_counts["WICKET KEEPER"] += 1
        elif "ALL ROUNDER" in role:
            role_counts["ALL ROUNDER"] += 1
            # All rounder counts as half bat/half bowl for variety
        elif "BOWLER" in role:
            role_counts["BOWLER"] += 1
        else:
            role_counts["BATSMAN"] += 1
            
    # --- Black Box Logic Penalties ---
    final_score = total_ppi
    
    # 1. Must have a Wicket Keeper
    if role_counts["WICKET KEEPER"] == 0:
        final_score -= 50  # Heavy penalty
        
    # 2. Bowling Depth (Min 5 bowling options)
    # Bowlers + All Rounders
    bowling_options = role_counts["BOWLER"] + role_counts["ALL ROUNDER"]
    if bowling_options < 5:
        penalty = (5 - bowling_options) * 10
        final_score -= penalty
        
    # 3. Batting Depth (Min 5 solid batters)
    # Batters + WK + All Rounders
    batting_options = role_counts["BATSMAN"] + role_counts["WICKET KEEPER"] + role_counts["ALL ROUNDER"]
    if batting_options < 5:
        final_score -= 20

    return {
        "score": round(final_score, 1),
        "raw_ppi": total_ppi,
        "composition": role_counts
    }
