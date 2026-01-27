from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
import string

from .models import Player, Team, Auction, Room, Participant, ChatMessage
from .serializers import PlayerSerializer, TeamSerializer, AuctionSerializer
from django.views.decorators.csrf import csrf_exempt


from .services.team_evaluator import evaluate_team

class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all().order_by("set_no")
    serializer_class = PlayerSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class AuctionViewSet(viewsets.ModelViewSet):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer


# ---------------- ROOM APIs ---------------- #
@csrf_exempt
@api_view(["POST"])
def create_room(request):
    host_name = request.data.get("host_name")
    team = request.data.get("team")

    if not host_name or not team:
        return Response({"error": "Host name and team required"}, status=400)

    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

    room = Room.objects.create(code=code, host_name=host_name)

    # 👇 Register host as participant
    Participant.objects.create(
        room=room,
        username=host_name,
        team=team,
        is_host=True
    )

    return Response({"code": room.code})


@csrf_exempt
@api_view(["POST"])
def join_room(request):
    code = request.data.get("code")
    username = request.data.get("username")
    team = request.data.get("team")

    if not all([code, username, team]):
        return Response({"error": "Missing data"}, status=400)

    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)

    if Participant.objects.filter(room=room, team=team).exists():
        return Response({"error": "Team already taken"}, status=409)

    Participant.objects.create(
        room=room,
        username=username,
        team=team,
        is_host=False
    )

    return Response({"message": "Joined successfully"})


# ---------------- AUCTION CONTROL ---------------- #

def move_to_next_player(room):
    """Helper function to move auction to next player"""
    if not room.current_player:
        return False
        
    current_set = room.current_player.set_no
    current_id = room.current_player.id
    
    # 1. Try to find next player in the SAME set (same set_no, higher ID)
    next_player = Player.objects.filter(
        set_no=current_set, 
        id__gt=current_id
    ).order_by('id').first()
    
    # 2. If no more in same set, find first player in NEXT set (higher set_no)
    if not next_player:
        next_player = Player.objects.filter(
            set_no__gt=current_set
        ).order_by('set_no', 'id').first()
    
    if next_player:
        room.current_player = next_player
        room.current_bid = next_player.base_price
        room.highest_bidder = None
        room.timer = room.default_timer_duration
        room.last_timer_update = timezone.now()
        room.save()
        return True
    else:
        # No more players - end auction
        room.is_live = False
        room.save()
        return False


@csrf_exempt
@api_view(["POST"])
def start_auction(request):
    code = request.data.get("code")

    if not code:
        return Response({"error": "Room code required"}, status=400)

    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)

    # Set first player if not set
    if not room.current_player:
        first_player = Player.objects.order_by("set_no").first()
        if not first_player:
            return Response({"error": "No players found in database"}, status=404)
        room.current_player = first_player
        room.current_bid = first_player.base_price

    # Set room to live
    room.is_live = True
    room.is_paused = False
    room.timer = room.default_timer_duration  # ✅ Use dynamic timer
    room.last_timer_update = timezone.now()
    room.save()

    return Response({
        "message": "Auction started",
        "room": room.code,
    })


@csrf_exempt
@api_view(["POST"])
def pause_auction(request):
    """Pause or resume auction (host only)"""
    code = request.data.get("code")
    
    if not code:
        return Response({"error": "Room code required"}, status=400)
    
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)
    
    # Toggle pause state
    room.is_paused = not room.is_paused
    
    if room.is_paused:
        # Calculate remaining time and freeze it
        if room.last_timer_update:
            elapsed = (timezone.now() - room.last_timer_update).total_seconds()
            room.timer = max(0, room.timer - int(elapsed))
    else:
        # Resume - reset last update time
        room.last_timer_update = timezone.now()
    
    room.save()
    
    return Response({
        "is_paused": room.is_paused,
        "timer": room.timer
    })


@csrf_exempt
@api_view(["POST"])
def update_room_settings(request):
    """Update room settings (Host only)"""
    code = request.data.get("code")
    timer_duration = request.data.get("timer_duration")
    
    if not code or not timer_duration:
        return Response({"error": "Missing data"}, status=400)
        
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)
        
    try:
        room.default_timer_duration = int(timer_duration)
        room.save()
        return Response({"message": "Settings updated", "timer": room.default_timer_duration})
    except ValueError:
        return Response({"error": "Invalid timer value"}, status=400)


@csrf_exempt
@api_view(["POST"])
def place_bid(request):
    code = request.data.get("code")
    team = request.data.get("team")
    amount = request.data.get("amount")

    print(f"\n{'='*60}")
    print(f"PLACE BID REQUEST")
    print(f"{'='*60}")
    print(f"Team: {team}")
    print(f"Amount: {amount}")
    print(f"{'='*60}\n")

    if not all([code, team, amount]):
        return Response({"error": "Missing data"}, status=400)

    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)
    
    print(f"Current Room State:")
    print(f"  Current Bid: {room.current_bid}")
    print(f"  Highest Bidder: {room.highest_bidder}")
    print(f"  Player: {room.current_player.name if room.current_player else 'None'}")
    
    # Check if paused
    if room.is_paused:
        return Response({"error": "Auction is paused"}, status=403)

    # Fetch participant
    try:
        participant = Participant.objects.get(room=room, team=team)
    except Participant.DoesNotExist:
        return Response({"error": "Team not found in room"}, status=403)

    # ❌ Squad Size Check (Max 25)
    if participant.squad_count >= 25:
        print(f"  ❌ Squad Limit Exceeded for {team}: {participant.squad_count}/25")
        return Response({"error": "Squad Limit (25) Reached!"}, status=403)
        
    # ❌ Same team cannot overbid itself
    if room.highest_bidder == team:
        print(f"  ❌ {team} already has highest bid!")
        return Response({" error": "You already have highest bid"}, status=403)
    
    # ❌ OS LIMIT CHECK checks
    if room.current_player and room.current_player.country.lower() != "india":
        # Check if team already has 8 OS players
        # Note: We rely on the finalized auction data for this count
        try:
            team_obj = Team.objects.get(name=team)
            os_count = Auction.objects.filter(
                room=room,
                team=team_obj,
                is_finalized=True
            ).exclude(player__country__iexact='India').count()
            
            if os_count >= 8:
                print(f"  ❌ OS Limit Exceeded for {team}: {os_count}/8")
                return Response({"error": "Overseas Player Limit (8) Reached!"}, status=403)
        except Team.DoesNotExist:
            pass # Should not happen if participant exists

    # ❌ Budget check
    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return Response({"error": "Invalid bid amount"}, status=400)
    
    # Convert budget from Crores to Lakhs (1 Cr = 10,000 Lakhs)
    budget_in_lakhs = participant.budget * 10000
    
    print(f"  Team Budget: ₹{participant.budget} Cr (₹{budget_in_lakhs}L)")
    print(f"  Bid Amount: ₹{amount}L")
    
    if budget_in_lakhs < amount:
        print(f"  ❌ Insufficient budget!")
        return Response({"error": "Insufficient budget"}, status=403)
    
    # ✅ ONLY Update room state - DO NOT create Auction record yet!
    # Auction record is created only when player is SOLD (finalized)
    room.current_bid = amount
    room.highest_bidder = team
    room.timer = room.default_timer_duration  # ✅ Use dynamic timer
    room.last_timer_update = timezone.now()
    room.save()
    
    print(f"  ✅ Bid accepted! New bid: ₹{amount}L by {team}")
    print(f"{'='*60}\n")

    return Response({"message": "Bid accepted", "new_timer": room.default_timer_duration})


@csrf_exempt
@api_view(["POST"])
def sell_player(request):
    """Finalize current player sale and move to next"""
    code = request.data.get("code")
    
    if not code:
        return Response({"error": "Room code required"}, status=400)
    
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)
    
    # Update participant budget and squad if sold
    if room.highest_bidder:
        participant = Participant.objects.get(room=room, team=room.highest_bidder)
        team_obj, _ = Team.objects.get_or_create(name=room.highest_bidder)
        
        # ✅ CREATE FINALIZED Auction record
        Auction.objects.create(
            room=room,
            player=room.current_player,
            team=team_obj,
            price=room.current_bid,
            is_finalized=True
        )
        
        # ✅ FIX: Deduct budget correctly (1 Cr = 100 Lakhs, not 10000)
        participant.budget -= Decimal(str(room.current_bid)) / Decimal('100')
        participant.squad_count += 1
        participant.save()
    
    # Move to next player
    has_next = move_to_next_player(room)
    
    if has_next:
        return Response({"message": "Player sold, moved to next"})
    else:
        return Response({"message": "Auction complete - no more players"})


# ---------------- STATE SYNC ---------------- #

@csrf_exempt
@api_view(["GET"])
def get_room_state(request, code):
    """Get complete synchronized room state"""
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)

    # Calculate current timer value
    if room.is_live and not room.is_paused and room.last_timer_update:
        elapsed = (timezone.now() - room.last_timer_update).total_seconds()
        current_timer = max(0, room.timer - int(elapsed))
        
        # ✅ NEW LOGIC: Handle sold/unsold status with 2-second delay
        if current_timer == 0 and not room.sold_status:
            # Timer just hit 0 - mark as SOLD or UNSOLD (don't move to next player yet!)
            if room.highest_bidder:
                room.sold_status = 'SOLD'
                room.sold_team = room.highest_bidder
                room.sold_price = room.current_bid
            else:
                room.sold_status = 'UNSOLD'
                room.sold_team = None
                room.sold_price = None
            
            room.sold_at = timezone.now()
            room.save()
        
        elif room.sold_status and room.sold_at:
            # Check if 1 second has elapsed since sold/unsold/skipped was set
            time_since_sold = (timezone.now() - room.sold_at).total_seconds()
            
            if time_since_sold >= 1:  # ✅ Changed from 2 seconds to 1 second
                # 1 second has passed - now finalize and move to next player
                if room.sold_status == 'SOLD':
                    # Get participant and team objects
                    participant = Participant.objects.get(room=room, team=room.sold_team)
                    team_obj, _ = Team.objects.get_or_create(name=room.sold_team)
                    
                    # ✅ CREATE FINALIZED Auction record (player is SOLD!)
                    Auction.objects.create(
                        room=room,
                        player=room.current_player,
                        team=team_obj,
                        price=room.sold_price,
                        is_finalized=True
                    )
                    
                    # ✅ FIX: Update participant budget correctly (1 Cr = 100 Lakhs, not 10000)
                    participant.budget -= Decimal(str(room.sold_price)) / Decimal('100')
                    participant.squad_count += 1
                    participant.save()
                    
                else:
                    # ✅ CREATE FINALIZED Auction record for UNSOLD/SKIPPED
                    Auction.objects.create(
                        room=room,
                        player=room.current_player,
                        team=None,
                        price=None,
                        is_finalized=True,
                        status=room.sold_status
                    )
                
                # Clear sold status and move to next player
                room.sold_status = None
                room.sold_at = None
                room.sold_team = None
                room.sold_price = None
                room.save()
                
                # Move to next player (whether sold, unsold, or skipped)
                move_to_next_player(room)
                current_timer = room.timer
    else:
        current_timer = room.timer

    # Get current player info with ALL details
    player_data = None
    bid_increment = 5  # Default smallest increment
    
    if room.current_player:
        # ✅ Calculate bid increment based on CURRENT BID (not base price!)
        # This allows increments to change dynamically as bidding progresses
        current = room.current_bid if room.current_bid > 0 else room.current_player.base_price
        
        if current >= 200:
            bid_increment = 20  # ₹200L+ → +₹20L
        elif current >= 100:
            bid_increment = 10  # ₹100L-199L → +₹10L
        else:
            bid_increment = 5   # Under ₹100L → +₹5L
        
        player_data = {
            "id": room.current_player.id,
            "name": room.current_player.name,
            "role": room.current_player.role,
            "country": room.current_player.country,
            "base_price": room.current_player.base_price,
            "age": room.current_player.age,
            "hand": room.current_player.hand,
            "bowling": room.current_player.bowling,
        }
    
    # Get user's current budget (if team is in request)
    user_budget = None
    team_name = request.GET.get('team', None)
    if team_name:
        try:
            participant = Participant.objects.get(room=room, team=team_name)
            user_budget = participant.budget  # In Crores
        except Participant.DoesNotExist:
            pass

    return Response({
        "room_code": room.code,
        "is_live": room.is_live,
        "is_paused": room.is_paused,
        "timer": current_timer,
        "default_timer": room.default_timer_duration,
        "current_bid": room.current_bid,
        "highest_bidder": room.highest_bidder,
        "current_player": player_data,
        "bid_increment": bid_increment,
        "user_budget": user_budget,  # User's current purse in Crores
        "sold_status": room.sold_status,  # 'SOLD', 'UNSOLD', or None
        "sold_team": room.sold_team,
        "sold_price": room.sold_price,
        "status": room.status,  # Workflow Status (LIVE, SELECTION, COMPLETED)
        "players_joined": room.participants.count(),
        # Assuming 10 is the limit for now as per user request example "4/10"
        # Ideally this should be a field in Room model, but fixing to 10 for demo.
        "total_players_limit": 10, 
    })


# ---------------- CHAT ---------------- #

@csrf_exempt
@api_view(["GET"])
def get_chat_messages(request, code):
    """Get all chat messages for a room"""
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)
    
    messages = room.messages.all()
    
    return Response([
        {
            "sender": msg.sender,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime("%H:%M:%S")
        }
        for msg in messages
    ])


@csrf_exempt
@api_view(["POST"])
def send_chat_message(request):
    """Send a chat message"""
    code = request.data.get("code")
    sender = request.data.get("sender")
    message = request.data.get("message")
    
    if not all([code, sender, message]):
        return Response({"error": "Missing data"}, status=400)
    
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)
    
    ChatMessage.objects.create(
        room=room,
        sender=sender,
        message=message
    )
    
    return Response({"status": "sent"})


# ---------------- OTHER ---------------- #

@csrf_exempt
@api_view(["GET"])
def check_qualification(request, code):
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)

    result = []

    for p in room.participants.all():
        status = "QUALIFIED" if p.squad_count >= 18 else "DISQUALIFIED"
        result.append({
            "team": p.team,
            "players": p.squad_count,
            "status": status
        })

    return Response(result)


@csrf_exempt
@api_view(["GET"])
def get_my_team(request, code, team_name):
    """Get list of players purchased by a specific team"""
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)
    
    try:
        team_obj = Team.objects.get(name=team_name)
    except Team.DoesNotExist:
        return Response([])  # No purchases yet
    
    # ✅ ONLY get FINALIZED auction records (sold players)
    purchases = Auction.objects.filter(
        room=room, 
        team=team_obj, 
        is_finalized=True  # ONLY SHOW SOLD PLAYERS!
    ).values('player__id', 'player__name', 'price', 'player__country').distinct()
    
    # Get unique players
    seen_players = set()
    result = []
    
    for purchase in purchases:
        if purchase['player__name'] not in seen_players:
            result.append({
                "id": purchase['player__id'],
                "name": purchase['player__name'],
                "price": purchase['price'],
                "country": purchase['player__country']
            })
            seen_players.add(purchase['player__name'])
    
    return Response(result)


@csrf_exempt
@api_view(["POST"])
def skip_player(request):
    """Skip current player and move to next immediately"""
    code = request.data.get("code")
    
    if not code:
        return Response({"error": "Room code required"}, status=400)
    
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)
    
    if not room.current_player:
        return Response({"error": "No current player to skip"}, status=400)
    
    # Set SKIPPED status (similar to SOLD/UNSOLD)
    room.sold_status = 'SKIPPED'
    room.sold_at = timezone.now()
    room.save()
    
    return Response({"message": "Player skipped", "status": "SKIPPED"})


@csrf_exempt
@api_view(["POST"])
def end_auction(request):
    """End the auction"""
    code = request.data.get("code")
    
    if not code:
        return Response({"error": "Room code required"}, status=400)
    
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)
    
    # End the auction and move to SELECTION phase
    room.is_live = False
    room.is_paused = False
    room.status = 'SELECTION'  # Update status
    room.save()
    
    # 1. QUALIFICATION CHECK
    participants = Participant.objects.filter(room=room)
    qualified_count = 0
    
    for p in participants:
         # Count FINALIZED purchases
         squad_size = Auction.objects.filter(room=room, team__name=p.team, is_finalized=True).count()
         p.squad_count = squad_size # Ensure accurate count
         
         if squad_size >= 18:
             p.is_qualified = True
             qualified_count += 1
         else:
             p.is_qualified = False
         p.save()
    
    return Response({
        "message": "Auction ended. Moving to Selection Phase.",
        "qualified_count": qualified_count
    })


@csrf_exempt
@api_view(["POST"])
def submit_team(request):
    """Submit Playing XI for evaluation"""
    code = request.data.get("code")
    team_name = request.data.get("team")
    player_ids = request.data.get("player_ids")  # List of 11 IDs
    
    if not all([code, team_name, player_ids]):
        return Response({"error": "Missing data"}, status=400)
        
    try:
        room = Room.objects.get(code=code)
        participant = Participant.objects.get(room=room, team=team_name)
    except (Room.DoesNotExist, Participant.DoesNotExist):
        return Response({"error": "Invalid room or team"}, status=404)
        
    if not participant.is_qualified:
        return Response({"error": "You are not qualified to participate"}, status=403)
        
    if len(player_ids) != 11:
        return Response({"error": f"You MUST select exactly 11 players (Selected: {len(player_ids)})"}, status=400)
        
    # Fetch players
    selected_players = Player.objects.filter(id__in=player_ids)
    if selected_players.count() != 11:
        return Response({"error": "Invalid player IDs provided"}, status=400)
        
    # 1. Save Playing XI
    participant.playing_xi.set(selected_players)
    
    # 2. BLACK BOX EVALUATION
    eval_result = evaluate_team(selected_players)
    participant.final_score = eval_result['score']
    participant.save()
    
    # 3. Check if ALL qualified participants have submitted
    # Count qualified participants
    total_qualified = Participant.objects.filter(room=room, is_qualified=True).count()
    # Count participants with non-zero score (submitted)
    total_submitted = Participant.objects.filter(room=room, is_qualified=True, final_score__gt=0).count()
    
    if total_submitted >= total_qualified:
        room.status = 'COMPLETED'
        room.save()
        return Response({"message": "Team submitted", "status": "COMPLETED"})
        
    return Response({"message": "Team submitted successfully", "status": "SELECTION"})


@csrf_exempt
@api_view(["GET"])
def get_winner(request, code):
    """Get final leaderboard"""
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room"}, status=404)
        
    if room.status != 'COMPLETED':
        return Response({"error": "Winner not yet declared"}, status=400)
        
    # Get leaderboard
    participants = Participant.objects.filter(room=room, is_qualified=True).order_by('-final_score')
    
    result = []
    rank = 1
    for p in participants:
        result.append({
            "rank": rank,
            "team": p.team,
            "score": p.final_score,  # We show score now, but logic was hidden!
            "username": p.username
        })
        rank += 1
        
    return Response(result)


@csrf_exempt
@api_view(["GET"])
def get_summary(request, code):
    """Get summary of all teams and their purchased players"""
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)
    
    # Get all participants (teams)
    participants = Participant.objects.filter(room=room)
    
    result = []
    
    for participant in participants:
        # Get team object
        try:
            team_obj = Team.objects.get(name=participant.team)
        except Team.DoesNotExist:
            # No purchases for this team yet
            result.append({
                "team": participant.team,
                "budget_remaining": float(participant.budget),
                "players_count": 0,
                "players": []
            })
            continue
        
        # Get all finalized purchases for this team
        purchases = Auction.objects.filter(
            room=room,
            team=team_obj,
            is_finalized=True
        ).select_related('player')
        
        players_list = []
        for purchase in purchases:
            players_list.append({
                "id": purchase.player.id,
                "name": purchase.player.name,
                "price": purchase.price,
                "role": purchase.player.role,
                "country": purchase.player.country
            })
        
        result.append({
            "team": participant.team,
            "budget_remaining": float(participant.budget),
            "players_count": len(players_list),
            "players": players_list
        })
    
    
    return Response(result)


@csrf_exempt
@api_view(["GET"])
def get_upcoming_players(request, code):
    """Get list of upcoming players (not yet auctioned)"""
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)
    
    current_set = room.current_player.set_no if room.current_player else -1
    current_id = room.current_player.id if room.current_player else -1
    
    # Get all upcoming players:
    # 1. Players in same set with higher ID
    same_set = Player.objects.filter(set_no=current_set, id__gt=current_id).order_by('id')
    
    # 2. Players in higher sets
    next_sets = Player.objects.filter(set_no__gt=current_set).order_by('set_no', 'id')
    
    # Combine (list concatenation)
    upcoming = list(same_set) + list(next_sets)
    
    result = []
    for p in upcoming:
        result.append({
            "id": p.id,
            "name": p.name,
            "role": p.role,
            "country": p.country,
            "base_price": p.base_price,
            "set_no": p.set_no,
            "age": p.age,
            "hand": p.hand,
            "bowling": p.bowling
        })
        
    return Response(result)

@api_view(['GET'])
def get_unsold_players(request, code):
    try:
        room = Room.objects.get(code=code)
    except Room.DoesNotExist:
        return Response({"error": "Invalid room code"}, status=404)
        
    # Get players marked as UNSOLD or SKIPPED in the Auction table
    unsold_auctions = Auction.objects.filter(room=room, status__in=['UNSOLD', 'SKIPPED']).select_related('player')
    
    result = []
    for auction in unsold_auctions:
        p = auction.player
        result.append({
            "id": p.id,
            "name": p.name,
            "role": p.role,
            "country": p.country,
            "base_price": p.base_price,
            "set_no": p.set_no,
            "status": auction.status  # Include status
        })
        
    return Response(result)
