from django.shortcuts import render
from bangazonapi.models import Product

def expensive_products(request):
    products = Product.objects.filter(price__gte=1000)
    return render(request, "reports/expensive_products.html", {"products": products})
