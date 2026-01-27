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
    
    # End the auction
    room.is_live = False
    room.is_paused = False
    room.save()
    
    return Response({"message": "Auction ended"})


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
                "name": purchase.player.name,
                "price": purchase.price,
                "role": purchase.player.role
            })
        
        result.append({
            "team": participant.team,
            "budget_remaining": float(participant.budget),
            "players_count": len(players_list),
            "players": players_list
        })
    
    return Response(result)
