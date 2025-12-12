from django.urls import path
from .views import *


urlpatterns = [
    path('auth/register/', CreateUserView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/verify/', VerifyUserView.as_view(), name='verify'),
    path('members/profile/', MemberProfileView.as_view(), name='member-profile'),
    path('games/', GameList.as_view(), name='game-list'),
    path('game-copies/', GameCopyList.as_view(), name='game-copy-list'),
    path('my-game-copies/', MyGameCopiesView.as_view(), name='my-game-copies'),
    path('game-copies/<int:id>/', GameCopyDetail.as_view(), name='game-copy-detail'),
    path('reservations/', ReservationListCreate.as_view(), name='reservation-list'),
    path('reservations/<int:reservation_id>/respond/', ReservationResponseView.as_view(), name='reservation-respond'),
    path('reservations/<int:reservation_id>/pickup/', PickUpGameView.as_view(), name='pickup-game'),
    path('reservations/<int:reservation_id>/return/', ReturnGameView.as_view(), name='return-game'),
    path('ratings/user/', CreateUserRatingView.as_view(), name='create-user-rating'),
    path('ratings/game/', CreateGameRatingView.as_view(), name='create-game-rating'),
    path('categories/', CategoryList.as_view(), name='category-list'),
]