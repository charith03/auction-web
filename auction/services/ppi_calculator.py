import random

def calculate_ppi(player):
    """
    Calculates the Player Power Index (PPI) for a given player.
    
    Logic:
    1. If stats (runs/wickets) exist, use detailed formula.
    2. Fallback: Use Base Price + Random Variance.
    
    Formula is deterministic for the same input but has 'hidden' complexity.
    """
    
    # 1. Base Score from Base Price (Market Value)
    # Map 20 Lakhs -> 200 Crores to a 0-100 scale approximately
    # Max base price is usually 200 Lakhs (2 Crores). 
    # But auction price might be higher. We stick to intrinsic value (Base Price).
    
    normalized_price = min(player.base_price / 200.0, 1.0) * 100  # 0 to 100
    base_score = normalized_price 
    
    # 2. Role Bonus
    role_bonus = 0
    role = player.role.upper()
    if "ALL ROUNDER" in role:
        role_bonus = 15
    elif "WICKET KEEPER" in role:
        role_bonus = 10
    elif "BOWLER" in role or "BATSMAN" in role:
        role_bonus = 5
        
    # 3. "Hidden" Potential (Random but deterministic based on name hash)
    # We use a hash of the name so it's always the same for the same player check
    random.seed(player.name) 
    hidden_potential = random.randint(-10, 20)
    
    # 4. Stat-Based Adjustment (If data exists)
    stat_score = 0
    if player.batting_runs > 0 or player.wickets > 0:
        # Simple T20 Formula
        bat_score = (player.batting_avg * 0.4) + (player.strike_rate * 0.2)
        bowl_score = (player.wickets * 2.0) + (10 - player.economy) * 2
        stat_score = max(bat_score, bowl_score)
        
        # Blended Score if stats exist
        final_ppi = (stat_score * 0.7) + (role_bonus * 0.3)
    else:
        # Fallback Score
        final_ppi = (base_score * 0.6) + (role_bonus * 0.2) + hidden_potential
        
    # Cap between 10 and 99
    final_ppi = max(10, min(99, final_ppi))
    
    return round(final_ppi, 1)
