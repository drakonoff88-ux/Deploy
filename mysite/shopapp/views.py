from csv import DictWriter
from timeit import default_timer

from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from .common import save_csv_products
from .forms import ProductForm
from .models import Product, Order, ProductImage


class ShopIndexView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ('Laptop', 1999),
            ('Desktop', 2999),
            ('Smartphone', 999),
        ]
        context = {
            "time_running": default_timer(),
            "products": products,
        }
        return render(request, 'shopapp/shop-index.html', context=context)


class ProductDetailsView(DetailView):
    template_name = "shopapp/products-details.html"
    queryset = Product.objects.prefetch_related("images")
    context_object_name = "product"


class ProductsListView(ListView):
    template_name = "shopapp/products-list.html"
    context_object_name = "products"
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(CreateView):
    model = Product
    fields = "name", "price", "description", "discount", "preview"
    success_url = reverse_lazy("shopapp:products_list")


class ProductUpdateView(UpdateView):
    model = Product
    template_name_suffix = "_update_form"
    form_class = ProductForm

    def get_success_url(self):
        return reverse(
            "shopapp:product_details",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(
                product=self.object,
                image=image,
            )
        return response


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class OrdersListView(LoginRequiredMixin, ListView):
    template_name = "shopapp/order_list.html"
    context_object_name = "orders"
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
        .all()
    )


class OrderDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "shopapp.view_order"
    template_name = "shopapp/order_detail.html"
    context_object_name = "order"
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )


class UserOrdersListView(LoginRequiredMixin, ListView):
    template_name = 'shopapp/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        self.owner = get_object_or_404(User, id=self.kwargs['user_id'])
        return Order.objects.filter(user=self.owner).order_by('pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owner'] = self.owner
        return context


@login_required
def export_user_orders(request, user_id):
    # Генерируем уникальный ключ для кеша
    cache_key = f'user_orders_export_{user_id}'

    # Пытаемся получить данные из кеша
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"=== DATA FROM CACHE for user {user_id} ===")
        return JsonResponse(cached_data, safe=False)

    # Если данных в кеше нет, загружаем из базы
    print(f"=== DATA FROM DATABASE for user {user_id} ===")
    owner = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(user=owner).order_by('pk')

    # Вручную создаем JSON данные (без сериализатора DRF)
    orders_data = []
    for order in orders:
        order_data = {
            'id': order.id,
            'delivery_address': order.delivery_address,
            'promocode': order.promocode,
            'created_at': order.created_at.isoformat(),
            'user': order.user.username,
            'products': [
                {
                    'id': product.id,
                    'name': product.name,
                    'price': str(product.price)
                }
                for product in order.products.all()
            ]
        }
        orders_data.append(order_data)

    # Сохраняем в кеш на 5 минут (300 секунд)
    cache.set(cache_key, orders_data, timeout=300)

    print(f"=== DATA SAVED TO CACHE for user {user_id} ===")
    return JsonResponse(orders_data, safe=False)


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        products = Product.objects.order_by('pk').all()
        products_data = [
            {
                "pk": product.pk,
                "name": product.name,
                "price": str(product.price),
                "archived": product.archived,
            }
            for product in products
        ]
        return JsonResponse({"products": products_data})