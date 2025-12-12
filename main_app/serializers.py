from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class GameSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = '__all__'
    
    def get_average_rating(self, obj):
        ratings = GameRating.objects.filter(game=obj)
        if ratings:
            return sum([r.enjoyability for r in ratings]) / len(ratings)
        return None
    
    def get_total_ratings(self, obj):
        return GameRating.objects.filter(game=obj).count()

class ExpansionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expansion
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    total_lends = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = '__all__'
    
    def get_average_rating(self, obj):
        ratings = UserRating.objects.filter(ratee=obj)
        if ratings:
            total = sum([r.friendliness + r.deadline_respect + r.care_for_items for r in ratings])
            return total / (len(ratings) * 3)
        return None
    
    def get_total_lends(self, obj):
        return Reservation.objects.filter(owner=obj, status='accepted').count()

class GameCopySerializer(serializers.ModelSerializer):
    game = serializers.PrimaryKeyRelatedField(queryset=Game.objects.all())
    owner = MemberSerializer(read_only=True)
    expansions = serializers.SerializerMethodField()
    
    class Meta:
        model = GameCopy
        fields = '__all__'
    
    def get_expansions(self, obj):
        expansions = GameCopyExpansion.objects.filter(game_copy=obj)
        return ExpansionSerializer([e.expansion for e in expansions], many=True).data

class ReservationSerializer(serializers.ModelSerializer):
    game_copy = GameCopySerializer(read_only=True)
    borrower = MemberSerializer(read_only=True)
    owner = MemberSerializer(read_only=True)
    days_until_due = serializers.SerializerMethodField()
    
    class Meta:
        model = Reservation
        fields = '__all__'
    
    def get_days_until_due(self, obj):
        if obj.due_date:
            from datetime import date
            return (obj.due_date - date.today()).days
        return None

class UserRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRating
        fields = '__all__'
        read_only_fields = ('rater', 'created_date')

class GameRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRating
        fields = '__all__'
        read_only_fields = ('rater', 'created_date')