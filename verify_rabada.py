
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction_web.settings')
django.setup()

from auction.models import Player
p = Player.objects.filter(name__icontains='Rabada').first()
if p:
    print(f"Name: {p.name}")
    print(f"Age: {p.age}")
    print(f"Hand: {p.hand}")
    print(f"Bowling: {p.bowling}")
    print(f"Price: {p.base_price}")
else:
    print("Player not found")
