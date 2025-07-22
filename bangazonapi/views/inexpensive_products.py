# bangazonapi/views.py

from django.shortcuts import render
from bangazonapi.models import Product

def inexpensive_products(request):
    products = Product.objects.filter(price__lte=999)
    return render(request, "reports/inexpensive_products.html", { "products": products })
