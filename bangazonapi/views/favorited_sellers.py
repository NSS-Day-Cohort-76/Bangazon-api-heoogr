from bangazonapi.models import Customer

from django.shortcuts import render, get_object_or_404
from bangazonapi.models import Customer, Favorite


def favorited_sellers_report(request):
    customer_id = request.GET.get("customer")
    customer = get_object_or_404(Customer, pk=customer_id)
    # Get all Favorite objects for this customer
    favorites = Favorite.objects.filter(customer=customer).select_related("seller")
    sellers = [fav.seller for fav in favorites]

    context = {
        "customer": customer,
        "sellers": sellers,
    }
    return render(request, "reports/favorited_sellers.html", context)


# create html template report of each customer and their favorited sellers
# def generate_favorited_sellers_report():
#     customers = Customer.objects.all()
#     report_data = []

#     for customer in customers:
#         favorited_sellers = customer.favorited_sellers.all()
#         for seller in favorited_sellers:
#             report_data.append(
#                 {
#                     "customer.first_name": customer.first_name,
#                     "customer.last_name": customer.last_name,
#                     "customer.favorited_seller": seller.name,
#                 }
#             )
#     return report_data
