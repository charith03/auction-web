from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import Room, Player, Participant, Team, Auction, AuctionLog

class AuctionSystemTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Setup basic data
        self.player1 = Player.objects.create(name="Player A", role="BAT", base_price=200, country="India", set_no=1)
        self.player2 = Player.objects.create(name="Player B", role="BOWL", base_price=100, country="Australia", set_no=1)
        
        # Create Room
        self.room_data = {"host_name": "HostUser", "team": "CSK", "is_public": True}
        response = self.client.post('/api/create-room/', self.room_data, format='json')
        self.room_code = response.data['code']
        self.room = Room.objects.get(code=self.room_code)
        
        # Join Room
        self.client.post('/api/join-room/', {"code": self.room_code, "username": "Joiner", "team": "MI"}, format='json')
        
        self.host = Participant.objects.get(room=self.room, team="CSK")
        self.joiner = Participant.objects.get(room=self.room, team="MI")

    # --- 1. ROOM TESTS ---
    def test_create_public_room(self):
        """Test public room creation"""
        self.assertTrue(self.room.is_public)
        self.assertEqual(self.room.host_name, "HostUser")
        
    def test_create_private_room(self):
        """Test private room creation"""
        data = {"host_name": "PrivateHost", "team": "RR", "is_public": False}
        res = self.client.post('/api/create-room/', data, format='json')
        room = Room.objects.get(code=res.data['code'])
        self.assertFalse(room.is_public)

    def test_join_validation(self):
        """Test preventing duplicate team join"""
        res = self.client.post('/api/join-room/', {"code": self.room_code, "username": "Cheater", "team": "CSK"}, format='json')
        self.assertEqual(res.status_code, 409)  # Conflict

    # --- 2. AUCTION FLOW TESTS ---
    def test_start_auction(self):
        """Test starting auction sets initial state"""
        self.client.post('/api/start-auction/', {"code": self.room_code}, format='json')
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_live)
        self.assertEqual(self.room.current_player, self.player1)
        # Check log
        log = AuctionLog.objects.filter(room=self.room).first()
        self.assertIn("Auction Started", log.message)

    def test_place_bid(self):
        """Test bidding logic"""
        self.client.post('/api/start-auction/', {"code": self.room_code}, format='json')
        
        # Place valid bid
        bid_data = {"code": self.room_code, "team": "MI", "amount": 220}
        res = self.client.post('/api/place-bid/', bid_data, format='json')
        self.assertEqual(res.status_code, 200)
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.current_bid, 220)
        self.assertEqual(self.room.highest_bidder, "MI")
        self.assertEqual(self.room.timer, 15)  # Timer reset

    def test_place_bid_insufficient_budget(self):
        """Test preventing bid over budget"""
        self.client.post('/api/start-auction/', {"code": self.room_code}, format='json')
        
        # Set budget to low
        self.joiner.budget = Decimal('1.00') # 1 Cr = 100 Lakhs
        self.joiner.save()
        
        # Bid 200 Lakhs
        bid_data = {"code": self.room_code, "team": "MI", "amount": 200}
        res = self.client.post('/api/place-bid/', bid_data, format='json')
        self.assertEqual(res.status_code, 403)
        self.assertIn("Insufficient budget", res.data['error'])

    # --- 3. SELLING & SQUADS ---
    def test_sell_player_updates_state(self):
        """Test selling logic updates squad and budget"""
        self.client.post('/api/start-auction/', {"code": self.room_code}, format='json')
        
        # MI Bids 500L (5Cr)
        self.client.post('/api/place-bid/', {"code": self.room_code, "team": "MI", "amount": 500}, format='json')
        
        # Sell
        self.client.post('/api/sell-player/', {"code": self.room_code}, format='json')
        
        # Verify Auction Record
        auction = Auction.objects.filter(room=self.room, is_finalized=True).first()
        self.assertIsNotNone(auction)
        self.assertEqual(auction.price, 500)
        self.assertEqual(auction.team.name, "MI")
        
        # Verify Participant Update
        self.joiner.refresh_from_db()
        self.assertEqual(self.joiner.squad_count, 1)
        # Initial 120 - 5 = 115
        self.assertEqual(self.joiner.budget, Decimal('115.00')) 
        
        # Verify moved to next player
        self.room.refresh_from_db()
        self.assertEqual(self.room.current_player, self.player2)
        
    def test_skip_player(self):
        """Test skipping logic"""
        self.client.post('/api/start-auction/', {"code": self.room_code}, format='json')
        
        self.client.post('/api/skip-player/', {"code": self.room_code}, format='json')
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.sold_status, "SKIPPED")
        
        # Verify Log
        log = AuctionLog.objects.filter(room=self.room, message__contains="SKIPPED").exists()
        self.assertTrue(log)
