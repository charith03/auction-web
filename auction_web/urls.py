"""
URL configuration for auction_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from auction.views import (
    PlayerViewSet, TeamViewSet, AuctionViewSet, 
    create_room, join_room, place_bid, check_qualification, get_room_state,
    start_auction, pause_auction, sell_player, get_active_rooms,
    get_chat_messages, send_chat_message, get_my_team,
    skip_player, end_auction, get_summary, get_upcoming_players, update_room_settings,
    get_unsold_players, submit_team, get_winner, get_auction_logs
)


router = routers.DefaultRouter()
router.register(r'players', PlayerViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'auctions', AuctionViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/rooms/', get_active_rooms),
    path('api/create-room/', create_room),
    path('api/join-room/', join_room),
    path("api/start-auction/", start_auction),
    path("api/pause-auction/", pause_auction),
    path("api/place-bid/", place_bid),
    path("api/sell-player/", sell_player),
    path("api/skip-player/", skip_player),
    path("api/end-auction/", end_auction),
    path("api/check-qualification/<str:code>/", check_qualification),
    path("api/room-state/<str:code>/", get_room_state),
    path("api/chat/<str:code>/", get_chat_messages),
    path("api/send-message/", send_chat_message),
    path("api/my-team/<str:code>/<str:team_name>/", get_my_team),
    path("api/summary/<str:code>/", get_summary),
    path("api/upcoming-players/<str:code>/", get_upcoming_players),
    path("api/unsold-players/<str:code>/", get_unsold_players),
    path("api/update-settings/", update_room_settings),
    path("api/submit-xi/", submit_team),
    path("api/winner/<str:code>/", get_winner),
    path("api/logs/<str:code>/", get_auction_logs),
]




