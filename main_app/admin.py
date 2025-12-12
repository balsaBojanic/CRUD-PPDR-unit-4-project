from django.contrib import admin
from .models import Category, Game, GameCopy, Expansion, Member, Reservation, UserRating, GameRating

admin.site.register(Category)
admin.site.register(Game)
admin.site.register(GameCopy)
admin.site.register(Expansion)
admin.site.register(Member)
admin.site.register(Reservation)
admin.site.register(UserRating)
admin.site.register(GameRating)