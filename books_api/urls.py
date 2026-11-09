from django.urls import path

from books_api.views import (
	AuthorDetailView,
	AuthorListCreateView,
	BookDetailView,
	BookListCreateView,
	AvailableBookListView,
	BorrowedBookDetailView,
	BorrowedBookListCreateView,
	BorrowedBookReturnView,
)

urlpatterns = [
	path('authors/', AuthorListCreateView.as_view(), name='author-list'),
	path('authors/<int:pk>/', AuthorDetailView.as_view(), name='author-detail'),
	path('books/', BookListCreateView.as_view(), name='book-list'),
	path('books/available/', AvailableBookListView.as_view(), name='available-book-list'),
	path('books/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
	path('borrowed-books/', BorrowedBookListCreateView.as_view(), name='borrowed-book-list'),
	path('borrowed-books/<int:pk>/', BorrowedBookDetailView.as_view(), name='borrowed-book-detail'),
	path('borrowed-books/<int:pk>/return/', BorrowedBookReturnView.as_view(), name='borrowed-book-return'),
]
