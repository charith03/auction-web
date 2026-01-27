"""
DEBUG SCRIPT - Run this to check auction state
Usage: python debug_auction.py <room_code>
"""

import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_web.settings')
django.setup()

from auction.models import Room, Participant, Player

if len(sys.argv) < 2:
    print("Usage: python debug_auction.py <room_code>")
    sys.exit(1)

code = sys.argv[1]

try:
    room = Room.objects.get(code=code)
except Room.DoesNotExist:
    print(f"Room {code} not found!")
    sys.exit(1)

print("=" * 60)
print(f"ROOM: {room.code}")
print("=" * 60)
print(f"Is Live: {room.is_live}")
print(f"Is Paused: {room.is_paused}")
print(f"Current Player: {room.current_player.name if room.current_player else 'None'}")
print(f"Current Bid: ₹{room.current_bid}L")
print(f"Highest Bidder: {room.highest_bidder or 'None'}")
print(f"Timer: {room.timer}s")
print()

print("PARTICIPANTS:")
print("-" * 60)
for p in Participant.objects.filter(room=room):
    print(f"  {p.team:10s} - Budget: ₹{p.budget} Cr - Squad: {p.squad_count} players - Host: {p.is_host}")

print()
print("=" * 60)
print("RECENT BID CALCULATION:")
print("=" * 60)

if room.current_player:
    current = room.current_bid if room.current_bid > 0 else room.current_player.base_price
    
    if current >= 200:
        increment = 20
    elif current >= 100:
        increment = 10
    else:
        increment = 5
    
    print(f"Base Price: ₹{room.current_player.base_price}L")
    print(f"Current Bid: ₹{room.current_bid}L")
    print(f"Calculated Increment: +₹{increment}L")
    
    if room.highest_bidder:
        print(f"Next Bid: ₹{room.current_bid + increment}L")
    else:
        print(f"Next Bid (First): ₹{room.current_player.base_price}L")
