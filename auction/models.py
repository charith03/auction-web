from django.db import models


class Player(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20)  # Specialism (BOWLER, BAT, etc.)
    base_price = models.IntegerField()  # In Lakhs
    country = models.CharField(max_length=50)
    set_no = models.IntegerField(default=0)
    
    # Additional player details from Excel
    age = models.IntegerField(null=True, blank=True)
    hand = models.CharField(max_length=10, null=True, blank=True)  # RHB, LHB
    bowling = models.CharField(max_length=100, null=True, blank=True)  # e.g. "LEFT ARM Fast Medium"
    
    # Hidden Intelligence Layer (PPI) & Stats
    ppi = models.FloatField(default=0.0)  # Player Power Index
    batting_runs = models.IntegerField(default=0)
    batting_avg = models.FloatField(default=0.0)
    strike_rate = models.FloatField(default=0.0)
    wickets = models.IntegerField(default=0)
    economy = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=50, unique=True)
    budget = models.IntegerField(default=100)

    def __str__(self):
        return self.name


class Room(models.Model):
    code = models.CharField(max_length=10, unique=True)
    host_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    is_live = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)  # Public vs Private room
    
    # Workflow Status
    STATUS_CHOICES = [
        ('LIVE', 'Live Auction'),
        ('SELECTION', 'Selection Phase'),
        ('CALCULATING', 'Calculating Winner'),
        ('COMPLETED', 'Winner Declared')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='LIVE')
    
    current_player = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Server-side timer state
    default_timer_duration = models.IntegerField(default=15)  # Global setting for timer
    timer = models.IntegerField(default=15)  # seconds
    last_timer_update = models.DateTimeField(null=True, blank=True)
    
    # Current bid tracking
    current_bid = models.IntegerField(default=0)
    highest_bidder = models.CharField(max_length=10, null=True, blank=True)
    
    # Sold/Unsold status tracking (for 2-second display delay)
    sold_status = models.CharField(max_length=10, null=True, blank=True)  # 'SOLD', 'UNSOLD', or None
    sold_at = models.DateTimeField(null=True, blank=True)  # When player was marked sold/unsold
    sold_team = models.CharField(max_length=10, null=True, blank=True)  # Team that purchased (for SOLD)
    sold_price = models.IntegerField(null=True, blank=True)  # Final sale price (for SOLD)

    def __str__(self):
        return self.code



class Participant(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="participants")
    username = models.CharField(max_length=100)
    team = models.CharField(max_length=10)
    is_host = models.BooleanField(default=False)

    budget = models.DecimalField(max_digits=6, decimal_places=2, default=120.00)  # Budget in Crores with decimals
    squad_count = models.IntegerField(default=0)
    
    # Post-Auction Fields
    playing_xi = models.ManyToManyField(Player, blank=True, related_name="selected_by")
    is_qualified = models.BooleanField(default=False)  # True if squad >= 18
    final_score = models.FloatField(default=0.0)  # Black-Box Team Score

    class Meta:
        unique_together = ("room", "team")

    def __str__(self):
        return f"{self.username} ({self.team})"




class Auction(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)
    is_finalized = models.BooleanField(default=False)  # True only when process is done
    status = models.CharField(max_length=20, default='SOLD') # SOLD, UNSOLD, SKIPPED
    sold_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.player} -> {self.team} for {self.price}"

class Vote(models.Model):
   voter = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="votes_cast")
   candidate = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="votes_received")
   score = models.IntegerField(default=0)  # 1-10

   class Meta:
       unique_together = ('voter', 'candidate')


class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}"


class AuctionLog(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="logs")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.room.code}] {self.message}"

