from django.http import HttpResponseServerError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from bangazonapi.models import Store 
from django.contrib.auth.models import User



class UserSerializer(serializers.ModelSerializer):
    """JSON serializer for customer profile

    Arguments:
        serializers
    """

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

    permission_classes = [IsAuthenticated]

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
            stores = Store.objects.all()  # get all stores
            serializer = StoreSerializer(stores, many=True)  # many=True important!
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return HttpResponseServerError(ex)

