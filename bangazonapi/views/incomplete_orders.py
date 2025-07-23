from bangazonapi.models import Order, Customer, OrderProduct
from django.shortcuts import render, get_object_or_404


def incomplete_orders(request):
  status_incomplete = request.GET.get('status')
  orders = Order.objects.filter(payment_type=None)

  order_data = []
  for order in orders:
    total = sum(lineitem.product.price * lineitem.quantity
                for lineitem in order.lineitems.all())
    order_data.append({
      "order_id": order.id,
      "customer_name": f"{order.customer.user.first_name} {order.customer.user.last_name}",
      "total": total
    })

    context = {"orders": order_data}
    return render(request, "reports/incomplete.html", context)

  customer = Customer.objects.filter()
