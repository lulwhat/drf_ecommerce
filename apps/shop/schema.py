from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from core import settings


PRODUCT_SCHEMA_PARAMS = [
    OpenApiParameter(
        name="max_price",
        description="Filter products by MAX current price",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="min_price",
        description="Filter products by MIN current price",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="in_stock",
        description="Filter products by stock",
        required=False,
        type=OpenApiTypes.INT,
    ),
    OpenApiParameter(
        name="created_at",
        description="Filter products by date created",
        required=False,
        type=OpenApiTypes.DATE,
    ),
    OpenApiParameter(
        name="page_size",
        description="The amount of item per page you want to display. "
                    f"Defaults is {settings.REST_FRAMEWORK['PAGE_SIZE']}",
        required=False,
        type=OpenApiTypes.INT,
    ),
]
