from django.db import transaction
from rest_framework import serializers

from books_api.models import Author, Book, BorrowedBook


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'biography', 'created_at']
        read_only_fields = ['id', 'created_at']


class BookSerializer(serializers.ModelSerializer):
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id',
            'author',
            'title',
            'category',
            'description',
            'is_available',
            'created_at',
        ]
        read_only_fields = ['id', 'is_available', 'created_at']

    def get_is_available(self, book):
        if hasattr(book, '_is_available'):
            return book._is_available
        return not BorrowedBook.objects.filter(
            book_id=book.pk,
            returned_at__isnull=True,
        ).exists()


class BorrowedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowedBook
        fields = ['id', 'book', 'borrower_name', 'borrowed_at', 'returned_at']
        read_only_fields = ['id', 'borrowed_at', 'returned_at']

    def create(self, validated_data):
        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=validated_data['book'].pk)
            has_active_loan = BorrowedBook.objects.filter(
                book=book,
                returned_at__isnull=True,
            ).exists()
            if has_active_loan:
                raise serializers.ValidationError(
                    {'book': 'This book is currently unavailable.'}
                )

            borrowed_book = BorrowedBook.objects.create(
                book=book,
                borrower_name=validated_data['borrower_name'],
            )

        return borrowed_book

    def update(self, instance, validated_data):
        if 'book' in validated_data:
            raise serializers.ValidationError(
                {'book': 'The book cannot be changed after a borrowing record is created.'}
            )
        return super().update(instance, validated_data)