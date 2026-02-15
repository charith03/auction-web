
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_web.settings')
django.setup()

from auction.models import Room, Participant, Team, Auction
from auction.views import get_summary
from rest_framework.test import APIRequestFactory

try:
    room_code = 'RY212'
    if not Room.objects.filter(code=room_code).exists():
        print(f"Room {room_code} does not exist. Using first available room.")
        room = Room.objects.first()
        if room:
            room_code = room.code
            print(f"Using room: {room_code}")
        else:
            print("No rooms found.")
            sys.exit(0)

    print(f"Testing get_summary for room: {room_code}")
    
    room = Room.objects.get(code=room_code)
    participants = Participant.objects.filter(room=room)
    print(f"Participants: {participants.count()}")
    
    for p in participants:
        print(f"  Participant: {p.username} ({p.team})")
        try:
            t = Team.objects.get(name=p.team)
            print(f"    Team found: {t.name}")
        except Team.DoesNotExist:
            print(f"    Team NOT found: {p.team}")

        # specific logic from view
        try:
            budget_val = float(p.budget)
            print(f"    Budget: {budget_val}")
        except Exception as e:
            print(f"    Error converting budget: {e}")

    # Check auctions
    auctions = Auction.objects.filter(room=room)
    print(f"Auctions in room: {auctions.count()}")
    for a in auctions:
        try:
            print(f"  Auction: {a.id}, Player ID: {a.player_id}, Team ID: {a.team_id}")
            # Try to fetch related objects explicitly
            try:
                p = a.player
                print(f"    Player: {p.name}")
            except Exception as ignored:
                print(f"    Player fetch failed: {ignored}")
                
            try:
                t = a.team
                print(f"    Team: {t.name}")
            except Exception as ignored:
                print(f"    Team fetch failed: {ignored}")
                
        except Exception as e:
            print(f"  Error accessing auction {a.id}: {e}")

    # Check ALL auctions for orphans
    try:
        orphan_count = 0
        all_auctions = Auction.objects.all()
        print(f"Total Auctions in DB: {all_auctions.count()}")
        for a in all_auctions:
            try:
                _ = a.player
            except Exception:
                print(f"  Found orphan Auction {a.id} (missing player)")
                orphan_count += 1
        print(f"Total Orphans found: {orphan_count}")
        
    except Exception as e:
        print(f"Error checking orphans: {e}")

except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
