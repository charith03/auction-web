# Quick Check: Player Status in Database

## Problem
Timer resets but next player doesn't load → `move_to_next_player()` can't find next player

## Likely Causes
1. **Only 1 player in database** (Virat Kohli)
2. **Players missing `set_no` values**
3. **`set_no` values not sequential** (e.g., all players have `set_no=0`)

---

## Quick Fix: Add Players via Django Shell

Open terminal in `c:\Users\Lenovo\auction_web`:

```bash
python manage.py shell
```

Then paste this code:

```python
from auction.models import Player

# Check current players
print("Current players:")
for p in Player.objects.all().order_by('set_no'):
    print(f"  {p.set_no}: {p.name} - {p.role} - ₹{p.base_price}")

# If you need to add more players, use this:
players_to_add = [
    {"name": "MS Dhoni", "role": "WK", "country": "India", "base_price": 200, "set_no": 1},
    {"name": "Rohit Sharma", "role": "BAT", "country": "India", "base_price": 200, "set_no": 2},
    {"name": "Jasprit Bumrah", "role": "BOWL", "country": "India", "base_price": 200, "set_no": 3},
    {"name": "KL Rahul", "role": "WK", "country": "India", "base_price": 200, "set_no": 4},
    {"name": "Hardik Pandya", "role": "AR", "country": "India", "base_price": 200, "set_no": 5},
]

for player_data in players_to_add:
    Player.objects.get_or_create(**player_data)
    print(f"Added: {player_data['name']}")

print("\nTotal players:", Player.objects.count())
exit()
```

---

## OR: Fix Existing Players' set_no

If players exist but have wrong `set_no`:

```python
from auction.models import Player

# Assign sequential set_no values
for idx, player in enumerate(Player.objects.all(), start=0):
    player.set_no = idx
    player.save()
    print(f"Set {player.name} to set_no={idx}")

# Verify
print("\nVerified order:")
for p in Player.objects.all().order_by('set_no'):
    print(f"  {p.set_no}: {p.name}")

exit()
```

---

## Check Django Admin

You mentioned "all players were imported into super admin" - let's verify:

1. Go to `http://127.0.0.1:8000/admin/`
2. Click "Players"
3. **Check if there are multiple players**
4. **Check if they have different `set_no` values** (0, 1, 2, 3...)

**If all have `set_no=0`** → Run the "Fix Existing Players" script above

---

## Test After Fix

1. Restart Django server
2. Create new room
3. Start auction
4. Let timer hit 0 → Should load next player!
