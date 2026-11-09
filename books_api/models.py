from django.db import models

# Create your models here.
class Book(models.Model):
    author = models.ForeignKey(
        'Author',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='books',
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Author(models.Model):
    name = models.CharField(max_length=100)
    biography = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class BorrowedBook(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='borrow_records',
    )
    borrower_name = models.CharField(max_length=100)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
