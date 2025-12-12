from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from geopy.distance import geodesic
from django.utils import timezone
from .models import *
from .serializers import *
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
class CreateUserRatingView(generics.CreateAPIView):
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        reservation_id = self.request.data.get('reservation')
        reservation = Reservation.objects.get(id=reservation_id)
        rater = Member.objects.get(user=self.request.user)
        
        if rater == reservation.borrower:
            ratee = reservation.owner
        elif rater == reservation.owner:
            ratee = reservation.borrower
        else:
            raise PermissionDenied("You cannot rate for this reservation")
        
        serializer.save(rater=rater, ratee=ratee, reservation=reservation)

class CreateGameRatingView(generics.CreateAPIView):
    serializer_class = GameRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        reservation_id = self.request.data.get('reservation')
        reservation = Reservation.objects.get(id=reservation_id)
        rater = Member.objects.get(user=self.request.user)
        
        if rater != reservation.borrower:
            raise PermissionDenied("Only borrowers can rate games")
        
        serializer.save(rater=rater, game=reservation.game_copy.game, reservation=reservation)

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        member = Member.objects.create(user=user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': response.data,
            'member': MemberSerializer(member).data
        })

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            member = Member.objects.get(user=user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'member': MemberSerializer(member).data
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class VerifyUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = User.objects.get(username=request.user)
        member = Member.objects.get(user=user)
        refresh = RefreshToken.for_user(request.user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'member': MemberSerializer(member).data
        })

class MemberProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return Member.objects.get(user=self.request.user)

class GameList(generics.ListAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    
    def get_queryset(self):
        queryset = Game.objects.all()
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if category:
            queryset = queryset.filter(category__id=category)
            
        return queryset

class GameCopyList(generics.ListAPIView):
    serializer_class = GameCopySerializer
    
    def get_queryset(self):
        queryset = GameCopy.objects.filter(status='available')
        
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = self.request.query_params.get('radius', 10)
        
        if lat and lng:
            user_location = (float(lat), float(lng))
            nearby_copies = []
            
            for copy in queryset:
                if copy.owner.latitude and copy.owner.longitude:
                    owner_location = (copy.owner.latitude, copy.owner.longitude)
                    distance = geodesic(user_location, owner_location).km
                    if distance <= float(radius):
                        nearby_copies.append(copy.id)
            
            queryset = queryset.filter(id__in=nearby_copies)
        
        return queryset

class MyGameCopiesView(generics.ListCreateAPIView):
    serializer_class = GameCopySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        member = Member.objects.get(user=self.request.user)
        return GameCopy.objects.filter(owner=member)
    
    def perform_create(self, serializer):
        member = Member.objects.get(user=self.request.user)
        serializer.save(owner=member)

class GameCopyDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GameCopySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        member = Member.objects.get(user=self.request.user)
        return GameCopy.objects.filter(owner=member)

class ReservationListCreate(generics.ListCreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        member = Member.objects.get(user=self.request.user)
        return Reservation.objects.filter(
            Q(borrower=member) | Q(owner=member)
        ).order_by('-requested_date')
    
    def perform_create(self, serializer):
        game_copy_id = self.request.data.get('game_copy')
        game_copy = GameCopy.objects.get(id=game_copy_id)
        
        if game_copy.status != 'available':
            raise PermissionDenied("This game is not available for reservation")
        
        borrower = Member.objects.get(user=self.request.user)
        serializer.save(
            borrower=borrower,
            owner=game_copy.owner,
            game_copy=game_copy
        )

class ReservationResponseView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, reservation_id):
        reservation = Reservation.objects.get(id=reservation_id)
        member = Member.objects.get(user=request.user)
        
        if reservation.owner != member:
            raise PermissionDenied("You don't have permission to respond to this reservation")
        
        action = request.data.get('action')
        
        if action == 'accept':
            reservation.status = 'accepted'
            reservation.game_copy.status = 'lent'
            reservation.game_copy.save()
        elif action == 'decline':
            reservation.status = 'declined'
        
        reservation.response_date = timezone.now()
        reservation.save()
        
        return Response({'status': 'success', 'reservation_status': reservation.status})

class PickUpGameView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, reservation_id):
        reservation = Reservation.objects.get(id=reservation_id)
        member = Member.objects.get(user=request.user)
        
        if reservation.borrower != member:
            raise PermissionDenied("You don't have permission to pick up this game")
        
        reservation.picked_up_date = timezone.now()
        reservation.save()
        
        return Response({'status': 'success', 'picked_up': True})

class ReturnGameView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, reservation_id):
        reservation = Reservation.objects.get(id=reservation_id)
       