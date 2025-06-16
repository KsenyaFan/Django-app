"""
В этом модуле лежат различные наборы представлений.

Разные view интернет-магазина: по товарам, заказам и т.д.
"""
from csv import DictWriter
import logging
from timeit import default_timer

from django.contrib.auth.models import Group, User
from django.contrib.auth.mixins import LoginRequiredMixin, \
    PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest, \
    HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, \
    CreateView, UpdateView, DeleteView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django_filters.rest_framework import DjangoFilterBackend

from .common import save_csv_model
from .forms import GroupForm, ProductForm
from .models import Product, Order, ProductImage
from .serializers import ProductSerializers, OrderSerializers


log = logging.getLogger(__name__)


class LatestProductsFeed(Feed):
    title = "Shop products(latets)"
    description = "Updates on changes products shop"
    link = reverse_lazy("shopapp:products_list")

    def items(self):
        return (
            Product.objects
            .filter(created_at__isnull=False)
            .order_by("-created_at")[:5]
        )

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description[:100]


@extend_schema(description='Product views CRUD')
class ProductViewSet(ModelViewSet):
    """
    Набор представлений для действий над Product.

    Полный CDUD для сущностей товара.
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializers
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ["name", "description"]
    filterset_fields = [
        "name",
        "price",
        "description",
        "discount",
        "archived",
    ]
    ordering_fields = [
        "name",
        "price",
        "discount",
    ]


    @extend_schema(
        summary="Get one product by ID",
        description="Retrieves **product**, returns 404 if not found",
        responses={
            200: ProductSerializers,
            404: OpenApiResponse(description="Empty responce, product by ID not found"),
        }
    )

    @method_decorator(cache_page(60 * 2))
    def list(self, *args, **kwargs):
        # print(("hello products list"))
        return super().list(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(methods=["get"], detail=False)
    def download_csv(self, request:Request):
        response = HttpResponse(content_type="text/csv")
        filename = "products-export.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        queryset = self.filter_queryset(self.get_queryset())
        fields = [
            "name",
            "price",
            "description",
            "discount",
        ]
        queryset = queryset.only(*fields)
        writer = DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for product in queryset:
            writer.writerow({
                field:getattr(product, field)
                for field in fields
            })
        return response

    @action(
        methods=["post"],
        detail=False,
        parser_classes=[MultiPartParser]
    )
    def upload_csv(self, request:Request):
        products = save_csv_model(
            request.FILES['file'].file,
            encoding=request.encoding,
            model=self.model,
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializers
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ["delivery_address", "description"]
    filterset_fields = [
        "delivery_address",
        "promocode",
        "created_at",
        "user",
        "products",
    ]
    ordering_fields = [
        "id",
        "user",
        "created_at",
    ]

    @action(methods=["get"], detail=False)
    def download_csv(self, request: Request):
        response = HttpResponse(content_type="text/csv")
        filename = "orders-export.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        queryset = self.filter_queryset(self.get_queryset())
        fields = [
            "delivery_address",
            "promocode",
            "created_at",
            "user",
        ]
        queryset = queryset.only(*fields)
        writer = DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for order in queryset:
            writer.writerow({
                field: getattr(order, field)
                for field in fields
            })
        return response

    @action(
        methods=["post"],
        detail=False,
        parser_classes=[MultiPartParser]
    )
    def upload_csv(self, request: Request):
        orders = save_csv_model(
            request.FILES['file'].file,
            encoding=request.encoding,
            model=self.model,
        )
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class ShopIndexView(View):

    # @method_decorator(cache_page(60 * 2))
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ('Laptop', 1999),
            ('Desktop', 2999),
            ('Smartphone', 999),
        ]
        context = {
            "time_running": default_timer(),
            "products": products,
            "items": 1,
        }
        print("shop index context", context)
        # log.debug("Products for shop index: %s", products)
        # log.info("Rendering shop index")
        return render(request, 'shopapp/shop-index.html', context=context)


class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            "form": GroupForm(),
            "groups": Group.objects.prefetch_related('permissions').all(),
        }
        return render(request, 'shopapp/groups-list.html', context=context)

    def post(self, request: HttpRequest):
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect(request.path)


class ProductDetailsView(DetailView):
    template_name = "shopapp/products-details.html"
    # model = Product
    queryset = Product.objects.prefetch_related("images")
    context_object_name = "product"


class ProductsListView(ListView):
    template_name = "shopapp/products-list.html"
    context_object_name = "products"
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(UserPassesTestMixin, CreateView):
    def test_func(self):
        # return self.request.user.groups.filter(name="secret-group").exists()
        return self.request.user.is_superuser

    model = Product
    fields = "name", "price", "description", "discount", "preview"
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        return response


class ProductUpdateView(UserPassesTestMixin, UpdateView):
    permission_required = "shopapp.change_product"
    model = Product
    # fields = "name", "price", "description", "discount", "preview"
    template_name_suffix = "_update_form"
    form_class = ProductForm

    def test_func(self):
        product = self.get_object()
        user = self.request.user
        return user.is_superuser or (user.has_perm("shopapp.change_product")
                                     and product.created_by == user)

    def get_success_url(self):
        return reverse(
            "shopapp:product_details",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        responce = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(
                product=self.object,
                image=image,
            )

        return responce



class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class OrdersListView(LoginRequiredMixin, ListView):
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )


class OrderDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "shopapp.view_order"
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )


class OrderCreateView(CreateView):
    model = Order
    fields = "delivery_address", "promocode", "user", "products"
    success_url = reverse_lazy('shopapp:orders_list')


class OrderUpdateView(UpdateView):
    model = Order
    fields = "delivery_address", "promocode", "user", "products"
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse(
            "shopapp:order_details",
            kwargs={"pk": self.object.pk},
        )


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy('shopapp:orders_list')


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cache_key = "products_data_export"
        products_data = cache.get(cache_key)
        if products_data is None:
            products = Product.objects.order_by("pk").all()
            products_data = [
                {
                    "pk": product.pk,
                    "name": product.name,
                    "price": product.price,
                    "archived": product.archived,
                }
                for product in products
            ]
        cache.set(cache_key, products_data, 300)
        # elem = products_data[0]
        # name = elem["name"]
        # print(name)
        return JsonResponse({"products": products_data})


class OrdersExportView(View):

    def get(self, request: HttpRequest) -> JsonResponse:
        orders = Order.objects.order_by("id").all()
        orders_data = [
            {
                "id": order.id,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "user_id": order.user_id,
                "product_id": list(
                    order.products.values_list("id", flat=True)
                ),
            }
            for order in orders
        ]
        return JsonResponse({"orders": orders_data})


class UserOrdersListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "shopapp/user_orders_list.html"
    context_object_name = "user_orders"

    def  get_queryset(self):
        user_id = self.kwargs["user_id"]
        self.owner = get_object_or_404(User, pk=user_id)
        return Order.objects.filter(user=self.owner)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner
        return context


class UserOrdersExportView(View):

    # @method_decorator(cache_page(60 * 3))
    def get(self, request: HttpRequest, user_id) -> JsonResponse:
        cache_key = f"user_orders_{user_id}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return JsonResponse({"orders": cached_data})

        user = get_object_or_404(User, pk=user_id)
        orders = Order.objects.filter(user=user).order_by("pk")
        orders_data = [
            {
                "id": order.id,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "user_id": order.user_id,
                "products": [
                    {
                        "id": product.pk,
                        "name": product.name,
                        "price": float(product.price),
                    }
                    for product in order.products.all()
                ],
            }
            for order in orders
        ]

        cache.set(cache_key, orders_data, timeout=60 * 3)
        return JsonResponse({"orders": orders_data})
