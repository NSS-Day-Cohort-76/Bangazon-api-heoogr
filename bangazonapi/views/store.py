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
from bangazonapi.models import Favorite, Customer
from .product import ProductSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """JSON serializer for customer profile"""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        depth = 1


class StoreSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    can_be_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = ["id", "name", "description", "seller", "can_be_favorited"]
        read_only_fields = ["id", "seller"]

    def get_can_be_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        try:
            customer = Customer.objects.get(user=request.user)
            seller = Customer.objects.get(user=obj.seller)
            # User cannot favorite their own store
            if customer == seller:
                return False
            return not Favorite.objects.filter(
                customer=customer, seller=seller
            ).exists()
        except Customer.DoesNotExist:
            return False

    def create(self, validated_data):
        user = self.context["request"].user
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
            return Response(
                {"reason": "Store not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return Response({"reason": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a store"""
        try:
            store = Store.objects.get(pk=pk)
            if store.seller != request.user:
                return Response(
                    {"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN
                )

            store.name = request.data.get("name")
            store.description = request.data.get("description")
            store.save()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Store.DoesNotExist:
            return Response(
                {"reason": "Store not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return HttpResponseServerError(ex)

    def destroy(self, request, pk=None):
        """Delete a store"""
        try:
            store = Store.objects.get(pk=pk)
            if store.seller != request.user:
                return Response(
                    {"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN
                )

            store.delete()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Store.DoesNotExist:
            return Response(
                {"reason": "Store not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return Response(
                {"reason": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        """List all stores"""
        try:
            stores = Store.objects.all()
            serializer = StoreSerializer(stores, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return HttpResponseServerError(ex)

    @action(methods=["post", "delete"], detail=True)
    def favorite(self, request, pk=None):
        """Add or remove a store from user's favorites"""
        try:
            store = Store.objects.get(pk=pk)
            seller = Customer.objects.get(user=store.seller)
            customer = Customer.objects.get(user=request.user)

            if request.method == "POST":
                # Create a favorite if it doesn't exist
                Favorite.objects.get_or_create(customer=customer, seller=seller)
                return Response(
                    {"status": "Store added to favorites"},
                    status=status.HTTP_201_CREATED,
                )

            elif request.method == "DELETE":
                # Remove the favorite if it exists
                Favorite.objects.filter(customer=customer, seller=seller).delete()
                return Response(
                    {"status": "store unfavorited"}, status=status.HTTP_204_NO_CONTENT
                )

        except Store.DoesNotExist:
            return Response(
                {"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Customer not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return Response(
                {"reason": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """Get products for a specific store, categorized as selling/sold"""
        try:
            store = Store.objects.get(pk=pk)

            # Get all products for this store with sold count
            products = Product.objects.filter(customer__user=store.seller).annotate(
                sold_count=Count(
                    "lineitems", filter=Q(lineitems__order__payment_type__isnull=False)
                )
            )

            # Always return selling products
            selling = products.filter(quantity__gt=0)
            response_data = {
                "selling": ProductSerializer(
                    selling, many=True, context={"request": request}
                ).data,
            }

            # Only return 'sold' if viewer is the store owner
            if request.user == store.seller:
                sold = products.filter(quantity=0, sold_count__gt=0)
                response_data["sold"] = ProductSerializer(
                    sold, many=True, context={"request": request}
                ).data

            return Response(response_data, status=status.HTTP_200_OK)

        except Store.DoesNotExist:
            return Response(
                {"detail": "Store not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return Response(
                {"reason": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
