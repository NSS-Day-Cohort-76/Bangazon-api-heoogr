from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from bangazonapi.models import ProductRating, Customer, Product

class ProductRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRating
        fields = ['id', 'product', 'customer', 'rating', 'review']
        read_only_fields = ['id', 'customer']  # customer set automatically

class ProductRatings(ViewSet):

    def create(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.auth.user)
        product_id = request.data.get("product") or kwargs.get('pk')

        if not product_id:
            return Response({"product": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"product": "Invalid product ID."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['product'] = product_id  # Ensure product is in data

        serializer = ProductRatingSerializer(data=data)
        if serializer.is_valid():
            serializer.save(customer=customer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
