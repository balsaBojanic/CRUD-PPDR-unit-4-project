from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Game(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    min_players = models.IntegerField(default=1)
    max_players = models.IntegerField(default=1)
    playing_time = models.IntegerField()
    difficulty = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    
    def __str__(self):
        return self.name

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.URLField(blank=True)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.display_name or self.user.username

class GameCopy(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('lent', 'Lent'),
        ('hidden', 'Hidden'),
        ('retired', 'Retired'),
    )
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    owner = models.ForeignKey(Member, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    condition = models.TextField()
    notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.game.name} - {self.owner.display_name}"

class Expansion(models.Model):
    name = models.CharField(max_length=200)
    parent_game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='expansions')
    description = models.TextField()
    
    def __str__(self):
        return f"{self.name} (expansion for {self.parent_game.name})"

class GameCopyExpansion(models.Model):
    game_copy = models.ForeignKey(GameCopy, on_delete=models.CASCADE)
    expansion = models.ForeignKey(Expansion, on_delete=models.CASCADE)    
    class Meta:
        unique_together = ['game_copy', 'expansion']

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    )
    
    game_copy = models.ForeignKey(GameCopy, on_delete=models.CASCADE)
    borrower = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='borrowed_reservations')
    owner = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='owned_reservations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_date = models.DateTimeField(auto_now_add=True)
    response_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    picked_up_date = models.DateTimeField(null=True, blank=True)
    returned_date = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.status == 'accepted' and not self.due_date:
            self.due_date = timezone.now().date() + timedelta(days=14)
        super().save(*args, **kwargs)

class UserRating(models.Model):
    rater = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='given_ratings')
    ratee = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='received_ratings')
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    friendliness = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    deadline_respect = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    care_for_items = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['rater', 'reservation']

class GameRating(models.Model):
    rater = models.ForeignKey(Member, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    enjoyability = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    ease_of_learning = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    condition_accuracy = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['rater', 'game', 'reservation']