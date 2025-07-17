from django.http import HttpResponseServerError
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from bangazonapi.models import Store 
from bangazonapi.models import Product
from .product import ProductSerializer
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """JSON serializer for customer profile"""
    
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        depth = 1


class StoreSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)

    class Meta:
        model = Store
        fields = ['id', 'name', 'description', 'seller']
        read_only_fields = ['id', 'seller']

    def create(self, validated_data):
        user = self.context['request'].user
        return Store.objects.create(seller=user, **validated_data)


class Stores(ViewSet):
    """Handles store CRUD operations"""
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        # Only allow updating if current user is owner
        if self.request.user != serializer.instance.seller.user:
            raise PermissionDenied("You cannot edit a store you do not own.")
        serializer.save()

    # @action(detail=True, methods=['get'])
    # def products(self, request, pk=None):
    #     store = self.get_object()
    #     products = Product.objects.filter(store=store)
    #     serializer = ProductSerializer(products, many=True)
    #     return Response(serializer.data)

    def create(self, request):
        """Create a new store"""
        store = Store()
        store.seller = request.user
        store.name = request.data.get("name")
        store.description = request.data.get("description")

        try:
            store.save()
            serializer = StoreSerializer(store)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({"reason": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Retrieve a single store by ID"""
        try:
            store = Store.objects.get(pk=pk)
            serializer = StoreSerializer(store)
            return Response(serializer.data)
        except Store.DoesNotExist:
            return Response({"reason": "Store not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({"reason": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a store"""
        try:
            store = Store.objects.get(pk=pk)
            if store.seller != request.user:
                return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
            
            store.name = request.data.get("name")
            store.description = request.data.get("description")
            store.save()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Store.DoesNotExist:
            return Response({"reason": "Store not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def destroy(self, request, pk=None):
        """Delete a store"""
        try:
            store = Store.objects.get(pk=pk)
            if store.seller != request.user:
                return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
            
            store.delete()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Store.DoesNotExist:
            return Response({"reason": "Store not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({"reason": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request):
        """List all stores"""
        try:
            stores = Store.objects.all()
            serializer = StoreSerializer(stores, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return HttpResponseServerError(ex)

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """Get products for a specific store, categorized as selling/sold"""
        try:
            store = Store.objects.get(pk=pk)

            if store.seller != request.user:
                return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            # Get products for this store with sold count annotation
            products = Product.objects.filter(customer__user=store.seller).annotate(
                sold_count=Count(
                    "lineitems",
                    filter=Q(lineitems__order__payment_type__isnull=False)
                )
            )

            # Categorize products based on quantity and sales
            selling = products.filter(quantity__gt=0)
            sold = products.filter(quantity=0, sold_count__gt=0)

            return Response({
                "selling": ProductSerializer(selling, many=True, context={"request": request}).data,
                "sold": ProductSerializer(sold, many=True, context={"request": request}).data,
            }, status=status.HTTP_200_OK)

        except Store.DoesNotExist:
            return Response({"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({"reason": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)