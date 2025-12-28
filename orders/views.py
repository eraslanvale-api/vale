from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer

class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Müşteri sadece kendi siparişlerini görür
        queryset = Order.objects.filter(user=self.request.user).order_by('-created_at')
        
        status_group = self.request.query_params.get('group')
        if status_group == 'active':
            queryset = queryset.filter(status__in=[
                'scheduled', 'searching', 'accepted', 'assigned', 'on_way', 'in_progress'
            ])
        elif status_group == 'history':
            queryset = queryset.filter(status__in=['completed', 'cancelled'])
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Müşteri kendi siparişini, Sürücü atandığı veya havuzdaki siparişi görebilir
        user = self.request.user
        if user.role == 'Şoför': # Driver rolü kontrolü
             return Order.objects.all() # Sürücüler detay görebilsin (daha kısıtlı bir filtre eklenebilir)
        return Order.objects.filter(user=user)

# --- Driver Views ---

class DriverJobPoolView(generics.ListAPIView):
    """
    Sürücülerin havuzdaki (henüz atanmamış) işleri göreceği endpoint.
    Status: 'scheduled' veya 'searching' ve driver=None olanlar.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            status__in=['scheduled', 'searching'], 
            driver__isnull=True
        ).order_by('created_at')

class DriverMyJobsView(generics.ListAPIView):
    """
    Sürücünün kendi üstlendiği veya tamamladığı işler.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(driver=self.request.user).order_by('-created_at')

class DriverAcceptJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            with transaction.atomic():
                # Select for update ile kilitleyelim ki aynı anda iki kişi alamasın
                order = Order.objects.select_for_update().get(id=id)
                
                if order.driver is not None:
                    return Response(
                        {"error": "Bu görev başka bir sürücü tarafından alınmış."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Sürücüyü ata
                order.driver = request.user
                order.status = 'accepted'
                order.save()
                
                return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Görev bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

class DriverCompleteJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            order = Order.objects.get(id=id, driver=request.user)
            order.status = 'completed'
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Görev bulunamadı veya size ait değil."}, status=status.HTTP_404_NOT_FOUND)

