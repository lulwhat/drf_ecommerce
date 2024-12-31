from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.paginations import CustomPagination
from apps.common.permissions import (
    IsOwnerPermission, IsOwnerOrStaffPermission
)
from apps.common.utils import set_dict_attr
from apps.profiles.models import OrderItem, ShippingAddress, Order
from apps.sellers.models import Seller
from apps.shop.filters import ProductFilter
from apps.shop.models import Category, Product, Review
from apps.shop.schema import PRODUCT_SCHEMA_PARAMS
from apps.shop.serializers import (
    CategorySerializer, ProductSerializer, OrderItemSerializer,
    ToggleCartItemSerializer, OrderSerializer, CheckoutSerializer,
    CreateModifyReviewSerializer, GetReviewSerializer
)

tags = ["Shop"]


class CategoriesView(APIView):
    serializer_class = CategorySerializer

    @extend_schema(
        summary="Categories Fetch",
        description="""
            This endpoint returns all categories.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Category Create",
        description="""
            This endpoint create categories.
        """,
        tags=tags
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_cat = Category.objects.create(**serializer.validated_data)
            serializer = self.serializer_class(new_cat)
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)


class ProductsByCategoryView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="category_products",
        summary="Category Products Fetch",
        description="""
            This endpoint returns all products in a particular category.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response(
                data={"message": "Category does not exist!"},
                status=404
            )
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


class ProductsView(APIView):
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    @extend_schema(
        operation_id="all_products",
        summary="Product Fetch",
        description="""
            This endpoint returns all products.
        """,
        tags=tags,
        parameters=PRODUCT_SCHEMA_PARAMS,
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).all()
        filterset = ProductFilter(request.GET, queryset=products)
        if filterset.is_valid():
            paginator = self.pagination_class()
            queryset = paginator.paginate_queryset(filterset.qs, request)
            serializer = self.serializer_class(queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response(filterset.errors, status=400)


class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="""
            This endpoint returns all products of a particular seller.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response(
                data={"message": "Seller does not exist!"},
                status=404
            )
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)


class ProductView(APIView):
    serializer_class = ProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="product_detail",
        summary="Product Details Fetch",
        description="""
            This endpoint returns product details via slug.
        """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs['slug'])
        if not product:
            return Response(
                data={"message": "Product does not exist!"},
                status=404
            )
        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=200)


class CartView(APIView):
    permission_classes = [IsOwnerPermission]
    serializer_class = OrderItemSerializer

    @extend_schema(
        summary="Cart Items Fetch",
        description="""
            This endpoint returns all items in a user cart.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        order_items = OrderItem.objects.filter(
            user=user, order=None
        ).select_related(
            "product", "product__seller", "product__seller__user"
        )
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data)

    @extend_schema(
        summary="Toggle Item in cart",
        description="""
            This endpoint allows a user or guest to add/update/remove 
            an item in cart.
            If quantity is 0, the item is removed from cart
        """,
        tags=tags,
        request=ToggleCartItemSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ToggleCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quantity = data["quantity"]

        product = Product.objects.select_related(
            "seller", "seller__user"
        ).get_or_none(slug=data["slug"])
        if not product:
            return Response(
                {"message": "No Product with that slug"},
                status=404
            )
        order_item, created = OrderItem.objects.update_or_create(
            user=user,
            order_id=None,
            product=product,
            defaults={"quantity": quantity},
        )
        resp_message_substring = "Updated In"
        status_code = 200
        if created:
            status_code = 201
            resp_message_substring = "Added To"
        if order_item.quantity == 0:
            resp_message_substring = "Removed From"
            order_item.delete()
        data = None
        if resp_message_substring != "Removed From":
            order_item.product = product
            serializer = self.serializer_class(order_item)
            data = serializer.data
        return Response(
            data={
                "message": f"Item {resp_message_substring} Cart",
                "item": data
            },
            status=status_code
        )


class CheckoutView(APIView):
    permission_classes = [IsOwnerPermission]
    serializer_class = CheckoutSerializer

    @extend_schema(
        summary="Checkout",
        description="""
               This endpoint allows user to create an order 
               for which payment can then be made through.
               """,
        tags=tags,
        request=CheckoutSerializer,
    )
    def post(self, request, *args, **kwargs):
        def _append_shipping_details(shipping):
            fields_to_update = [
                "full_name",
                "email",
                "phone",
                "address",
                "city",
                "country",
                "zipcode",
            ]
            data = {}
            for field in fields_to_update:
                value = getattr(shipping, field)
                data[field] = value
            return data

        # Proceed to checkout
        user = request.user
        order_items = OrderItem.objects.filter(user=user, order=None)
        if not order_items.exists():
            return Response({"message": "No Items in Cart"}, status=404)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_address_id = data.get("shipping_address_id")
        if shipping_address_id:
            shipping = ShippingAddress.objects.get_or_none(
                id=shipping_address_id
            )
            if not shipping:
                return Response(
                    {"message": "No shipping address with that ID"},
                    status=404
                )

        order = Order.objects.create(
            user=user, **_append_shipping_details(shipping)
        )
        order_items.update(order=order)

        serializer = OrderSerializer(order)
        return Response(
            data={"message": "Checkout Successful", "item": serializer.data},
            status=200
        )


class ReviewView(APIView):
    permission_classes = [IsOwnerOrStaffPermission]

    @extend_schema(
        summary="Get product reviews",
        description="""
                This endpoint allows to retrieve all reviews of a product.
            """,
        tags=tags
    )
    def get(self, request, slug, *args, **kwargs):
        product = Product.objects.get_or_none(slug=slug)
        if not product:
            return Response(
                data={"message": "This product does not exist!"},
                status=404
            )
        reviews = GetReviewSerializer(
            Review.objects.filter(product=product),
            many=True
        )
        return Response(
            data={"message": f"List of reviews for product {slug}",
                  "item": reviews.data},
            status=200
        )

    @extend_schema(
        summary="Post a review",
        description="""
            This endpoint allows user to create review for a product.
        """,
        tags=tags,
        request=CreateModifyReviewSerializer
    )
    def post(self, request, slug, *args, **kwargs):
        serializer = CreateModifyReviewSerializer(data=request.data)
        if serializer.is_valid():
            product = Product.objects.get_or_none(slug=slug)
            if not product:
                return Response(
                    data={"message": "This product does not exist!"},
                    status=404
                )
            existing_review = Review.objects.filter(
                product=product
            ).get_or_none(user=request.user)
            if existing_review:
                return Response(
                    data={"message": "You already reviewed this product!",
                          "item": str(existing_review)},
                    status=400
                )
            product.update_rating(serializer.validated_data['rating'])
            Review.objects.create(
                user=request.user,
                product=product,
                **serializer.validated_data
            )
            return Response(
                data={
                    "message": f"Review for product {slug} is posted",
                    "item": serializer.validated_data
                },
                status=200
            )
        else:
            return Response(
                data={"message":
                      f"Request data is incorrect: {serializer.errors}"},
                status=400
            )

    @extend_schema(
        summary="Modify a review",
        description="""
                This endpoint allows user to modify their review of a product.
            """,
        tags=tags,
        request=CreateModifyReviewSerializer(partial=True)
    )
    def put(self, request, slug, *args, **kwargs):
        serializer = CreateModifyReviewSerializer(data=request.data)
        if serializer.is_valid():
            product = Product.objects.get_or_none(slug=slug)
            if not product:
                return Response(
                    data={"message": "This product does not exist!"},
                    status=404
                )
            review = Review.objects.filter(
                product=product
            ).get_or_none(user=request.user)
            if not review:
                return Response(
                    data={"message": "Review of the product is not found!"},
                    status=404
                )
            if serializer.data['rating'] != review.rating:
                product.update_rating(
                    review_rating=serializer.data['rating'],
                    old_rating=review.rating
                )
            review = set_dict_attr(review, serializer.data)
            review.save()
            return Response(
                data={"message": "Review is updated",
                      "item": serializer.data},
                status=200
            )
        else:
            return Response(
                data={"message":
                      f"Request data is incorrect: {serializer.errors}"},
                status=400
            )

    @extend_schema(
        summary="Delete a review",
        description="""
                This endpoint allows user to delete their review of a product.
            """,
        tags=tags
    )
    def delete(self, request, slug, *args, **kwargs):
        product = Product.objects.get_or_none(slug=slug)
        if not product:
            return Response(
                data={"message": "This product does not exist!"},
                status=404
            )
        review = Review.objects.filter(
            product=product
        ).get_or_none(user=request.user)
        if not review:
            return Response(
                data={"message": "Review of the product is not found!"},
                status=404
            )
        product.update_rating(review_rating=review.rating, delete=True)
        review.delete()
        return Response(
            data={"message": "Review is deleted successfully"},
            status=204
        )
