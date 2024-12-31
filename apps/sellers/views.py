from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsSellerPermission
from apps.common.utils import set_dict_attr
from apps.profiles.models import OrderItem, Order
from apps.sellers.models import Seller
from apps.sellers.serializers import SellerSerializer
from apps.shop.models import Product, Category
from apps.shop.serializers import (
    ProductSerializer, CreateProductSerializer, ModifyProductSerializer,
    CheckItemOrderSerializer, OrderSerializer
)

tags = ['Sellers']


class SellersView(APIView):
    serializer_class = SellerSerializer

    @extend_schema(
        summary="Apply to become a seller",
        description="""
            This endpoint allows a buyer to apply to become a seller.
        """,
        tags=tags)
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, partial=False)
        if serializer.is_valid():
            data = serializer.validated_data
            seller, _ = Seller.objects.update_or_create(user=user,
                                                        defaults=data)
            user.account_type = 'SELLER'
            user.save()
            serializer = self.serializer_class(seller)
            return Response(data=serializer.data, status=201)
        else:
            return Response(data=serializer.errors, status=400)


class ProductsBySellerView(APIView):
    permission_classes = [IsSellerPermission]
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="""
            This endpoint returns all products from a seller.
            Products can be filtered by name, sizes or colors.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(user=request.user,
                                            is_approved=True)
        if not seller:
            return Response(data={"message": "Access is denied"}, status=403)
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Create a product",
        description="""
            This endpoint allows a seller to create a product.
        """,
        tags=tags,
        request=CreateProductSerializer,
        responses=CreateProductSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateProductSerializer(data=request.data)
        seller = Seller.objects.get_or_none(user=request.user,
                                            is_approved=True)
        if not seller:
            return Response(data={"message": "Access is denied"}, status=403)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(
                    data={"message": "Category does not exist!"},
                    status=404
                )
            data['category'] = category
            data['seller'] = seller
            new_prod = Product.objects.create(**data)
            serializer = self.serializer_class(new_prod)
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)


class SellerProductView(APIView):
    permission_classes = [IsSellerPermission]
    serializer_class = ModifyProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        if product is not None:
            self.check_object_permissions(self.request, product)
        return product

    @extend_schema(
        summary='Modify a product',
        description="""
            This endpoint allows a seller to modify their product.
        """,
        tags=tags,
        request={'multipart/form-data': serializer_class},
        responses=serializer_class
    )
    def put(self, request, slug, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        product = self.get_object(slug=slug)

        if not product:
            return Response(
                data={'message': 'Product is not found'},
                status=404
            )
        if product.seller.slug != request.user.seller.slug:
            return Response(
                data={'message': 'This product does not belong to this user'},
                status=403
            )
        if serializer.is_valid():
            data = serializer.validated_data
            product = set_dict_attr(product, data)
            if (float(data.get('price_current'))
                    != float(product.price_current)):
                setattr(product, 'price_old', float(data.get('price_current')))
            product.save()
            full_serializer = ProductSerializer(product)
            return Response(full_serializer.data, status=200)
        else:
            return Response(
                data={'message': 'Incorrect request body'}, status=400
            )

    @extend_schema(
        summary='Delete a product',
        description="""
            This endpoint allows seller to delete their product.    
        """,
        tags=tags,
        request=CreateProductSerializer
    )
    def delete(self, request, slug, *args, **kwargs):
        product = Product.objects.get_or_none(slug=slug)

        if not product:
            return Response(
                data={'message': 'Product is not found'},
                status=404
            )
        if product.seller.slug != request.user.seller.slug:
            return Response(
                data={'message': 'This product does not belong to this user'},
                status=403
            )
        product.delete()
        return Response(
            data={'message': 'Product is deleted successfully'},
            status=204
        )


class SellerOrdersView(APIView):
    permission_classes = [IsSellerPermission]
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id="seller_orders",
        summary="Seller Orders Fetch",
        description="""
            This endpoint returns all orders for a particular seller.
        """,
        tags=tags
    )
    def get(self, request):
        seller = request.user.seller
        orders = (
            Order.objects.filter(
                order_items__product__seller=seller
            ).order_by("-created_at")
        )
        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=200)


class SellerOrderItemView(APIView):
    permission_classes = [IsSellerPermission]
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id="seller_orders_items_view",
        summary="Seller Item Orders Fetch",
        description="""
            This endpoint returns all items orders for a particular seller.
        """,
        tags=tags,

    )
    def get(self, request, **kwargs):
        seller = request.user.seller
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order:
            return Response(
                data={"message": "Order does not exist!"},
                status=404
            )
        order_items = OrderItem.objects.filter(
            order=order, product__seller=seller
        )
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data, status=200)
