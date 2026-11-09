from django.contrib import admin

from books_api.models import Author, Book

# Register your models here.
admin.site.register(Book)
admin.site.register(Author)
