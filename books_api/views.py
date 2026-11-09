from django.db import transaction
from django.db.models import BooleanField, Case, FilteredRelation, Q, Value, When
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from books_api.models import Author, Book, BorrowedBook
from books_api.serializers import (
    AuthorSerializer,
    BookSerializer,
    BorrowedBookSerializer,
)


def books_with_availability():
    return Book.objects.annotate(
        active_loan=FilteredRelation(
            'borrow_records',
            condition=Q(borrow_records__returned_at__isnull=True),
        ),
    ).annotate(
        _is_available=Case(
            When(active_loan__id__isnull=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    )


class BookPagination(PageNumberPagination):
    page_size = 5


class BookListCreateView(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    pagination_class = BookPagination

    def get_queryset(self):
        queryset = books_with_availability()
        params = self.request.query_params
        title = params.get('title')
        category = params.get('category')
        search = params.get('search')
        ordering = params.get('ordering', '-created_at')

        if title:
            queryset = queryset.filter(title__icontains=title)
        if category:
            queryset = queryset.filter(category__iexact=category)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(category__icontains=search)
                | Q(description__icontains=search)
            )

        ordering_field = ordering.lstrip('-')
        allowed_ordering_fields = {'id', 'title', 'category', 'created_at'}
        if ordering_field not in allowed_ordering_fields:
            ordering = '-created_at'

        return queryset.order_by(ordering, 'id')


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookSerializer

    def get_queryset(self):
        return books_with_availability()


class AvailableBookListView(generics.ListAPIView):
    serializer_class = BookSerializer
    pagination_class = BookPagination

    def get_queryset(self):
        return books_with_availability().filter(
            active_loan__id__isnull=True,
        ).order_by('title', 'id')


class AuthorListCreateView(generics.ListCreateAPIView):
    queryset = Author.objects.order_by('name', 'id')
    serializer_class = AuthorSerializer


class AuthorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def destroy(self, request, *args, **kwargs):
        author = self.get_object()
        try:
            self.perform_destroy(author)
        except ProtectedError:
            return Response(
                {'detail': 'Cannot delete an author while books reference them.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class BorrowedBookListCreateView(generics.ListCreateAPIView):
    serializer_class = BorrowedBookSerializer

    def get_queryset(self):
        return BorrowedBook.objects.filter(
            returned_at__isnull=True,
        ).select_related('book').order_by('-borrowed_at', 'id')


class BorrowedBookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BorrowedBook.objects.select_related('book')
    serializer_class = BorrowedBookSerializer

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            borrowed_book = get_object_or_404(
                BorrowedBook.objects.select_for_update(),
                pk=kwargs['pk'],
            )
            if borrowed_book.returned_at is None:
                return Response(
                    {'detail': 'Return this book before deleting its borrowing record.'},
                    status=status.HTTP_409_CONFLICT,
                )
            self.perform_destroy(borrowed_book)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BorrowedBookReturnView(APIView):
    def post(self, request, pk):
        with transaction.atomic():
            borrowed_book = get_object_or_404(
                BorrowedBook.objects.select_for_update(),
                pk=pk,
            )
            if borrowed_book.returned_at is not None:
                return Response(
                    {'detail': 'This book has already been returned.'},
                    status=status.HTTP_409_CONFLICT,
                )

            book = Book.objects.select_for_update().get(pk=borrowed_book.book_id)
            borrowed_book.returned_at = timezone.now()
            borrowed_book.save(update_fields=['returned_at'])

        return Response(BorrowedBookSerializer(borrowed_book).data)