from autoslug import AutoSlugField
from django.db import models

from apps.accounts.models import User
from apps.common.models import BaseModel, IsDeletedModel
from apps.sellers.models import Seller

RATING_CHOICES = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5))


class Category(BaseModel):
    """
    Represents a product category.

    Attributes:
        name (str): The category name, unique for each instance.
        slug (str): The slug generated from the name, used in URLs.
        image (ImageField): An image representing the category.

    Methods:
        __str__():
            Returns the string representation of the category name.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    image = models.ImageField(upload_to='category_images/')

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "Categories"


class Product(IsDeletedModel):
    """
    Represents a product listed for sale.

    Attributes:
        seller (ForeignKey): The user who is selling the product.
        name (str): The name of the product.
        slug (str): The slug generated from the name, used in URLs.
        desc (str): A description of the product.
        price_old (Decimal): The original price of the product.
        price_current (Decimal): The current price of the product.
        category (ForeignKey): The category to which the product belongs.
        in_stock (int): The quantity of the product in stock.
        rating (FloatField): Rating of the product based on reviews.
        image1 (ImageField): The first image of the product.
        image2 (ImageField): The second image of the product.
        image3 (ImageField): The third image of the product.
    """

    seller = models.ForeignKey(Seller, on_delete=models.SET_NULL,
                               related_name="products", null=True)
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from="name", unique=True, db_index=True)
    desc = models.TextField()
    price_old = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_current = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name="products")
    in_stock = models.IntegerField(default=5)
    rating = models.FloatField(null=True)

    # Only 3 images are allowed
    image1 = models.ImageField(upload_to='product_images/')
    image2 = models.ImageField(upload_to='product_images/', blank=True)
    image3 = models.ImageField(upload_to='product_images/', blank=True)

    def update_rating(
            self, review_rating: int, old_rating: int = None, delete=False
    ):
        """Updates rating attribute for cases post/put/delete

        parameters:
            review_rating (int): rating of the review from 1 to 5
            old_rating (int): rating of the review before update
            delete (bool): if review is being deleted
        """
        reviews_count = Review.objects.all().count()
        match review_rating, old_rating, delete:
            # case for post
            case int(), None, False:
                if reviews_count > 0:
                    self.rating = (
                        (self.rating * reviews_count + review_rating)
                        / (reviews_count + 1)
                    )
                else:
                    self.rating = review_rating
            # case for put
            case int(), int(), False:
                if reviews_count > 1:
                    upd_total = self.rating
                    upd_total = (upd_total * reviews_count - old_rating)
                    upd_total = (
                        (upd_total + review_rating) / reviews_count
                    )
                    self.rating = upd_total
                else:
                    self.rating = review_rating
            # case for delete
            case int(), None, True:
                if reviews_count == 1:
                    self.rating = None
                else:
                    self.rating = (
                        (self.rating * reviews_count - review_rating)
                        / (reviews_count - 1)
                    )
            case _:
                raise TypeError("Incorrect function arguments")
        self.save()

    def __str__(self):
        return str(self.name)


class Review(IsDeletedModel):
    """
    Represents a review for a product.

    Attributes:
        user (ForeignKey) - User posting the review.
        product (ForeignKey) - Product being reviewed.
        rating (IntegerField) - Rating of the review, choices are 1-5.
        text (TextField) - Text of the review, may be blank.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name="reviews")
    rating = models.IntegerField(choices=RATING_CHOICES)
    text = models.TextField(null=True)

    def __str__(self):
        return (f"Review for {self.product} by user {self.user} "
                f"with rating {self.rating}")
