from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from bangazonapi.models import ProductRating, Customer

class ProductRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRating
        fields = ['id', 'product', 'customer', 'rating', 'review']
        read_only_fields = ['id', 'customer']  # customer set automatically

class ProductRatings(ViewSet):
    def create(self, request):
        customer = Customer.objects.get(user=request.auth.user)
        serializer = ProductRatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=customer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
