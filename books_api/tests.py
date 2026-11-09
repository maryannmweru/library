from rest_framework import status
from rest_framework.test import APITestCase

from books_api.models import Author, Book, BorrowedBook


class BookApiTests(APITestCase):
	list_url = '/api/books/'
	available_url = '/api/books/available/'
	author_list_url = '/api/authors/'
	borrowed_book_list_url = '/api/borrowed-books/'

	def create_book(self, title, category='Fiction', description='A book.'):
		author = Author.objects.create(name='Test Author', biography='Author bio.')
		return Book.objects.create(
			author=author,
			title=title,
			category=category,
			description=description,
		)

	def test_create_retrieve_update_and_delete_book(self):
		author = Author.objects.create(name='Frank Herbert', biography='An author.')
		response = self.client.post(
			self.list_url,
			{
				'author': author.id,
				'title': 'Dune',
				'category': 'Science Fiction',
				'description': 'A desert planet.',
			},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		book_id = response.data['id']
		detail_url = f'{self.list_url}{book_id}/'

		response = self.client.get(detail_url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['title'], 'Dune')

		response = self.client.patch(
			detail_url,
			{'title': 'Dune Messiah'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['title'], 'Dune Messiah')

		response = self.client.put(
			detail_url,
			{
				'author': author.id,
				'title': 'Children of Dune',
				'category': 'Science Fiction',
				'description': 'The next generation.',
			},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['title'], 'Children of Dune')

		response = self.client.delete(detail_url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(Book.objects.filter(pk=book_id).exists())

	def test_create_author_book_and_borrowed_book_through_api(self):
		author_response = self.client.post(
			self.author_list_url,
			{'name': 'Ursula Le Guin', 'biography': 'An author.'},
			format='json',
		)
		self.assertEqual(author_response.status_code, status.HTTP_201_CREATED)
		author_detail_url = f'{self.author_list_url}{author_response.data["id"]}/'

		author_detail_response = self.client.get(author_detail_url)
		self.assertEqual(author_detail_response.status_code, status.HTTP_200_OK)
		self.assertEqual(author_detail_response.data['name'], 'Ursula Le Guin')

		author_update_response = self.client.patch(
			author_detail_url,
			{'name': 'U. K. Le Guin'},
			format='json',
		)
		self.assertEqual(author_update_response.status_code, status.HTTP_200_OK)


		book_response = self.client.post(
			self.list_url,
			{
				'author': author_response.data['id'],
				'title': 'A Wizard of Earthsea',
				'category': 'Fantasy',
				'description': 'A young wizard learns magic.',
			},
			format='json',
		)
		self.assertEqual(book_response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(book_response.data['is_available'])

		author_delete_response = self.client.delete(author_detail_url)
		self.assertEqual(author_delete_response.status_code, status.HTTP_409_CONFLICT)

		borrowed_response = self.client.post(
			self.borrowed_book_list_url,
			{
				'book': book_response.data['id'],
				'borrower_name': 'Alex Reader',
			},
			format='json',
		)
		self.assertEqual(borrowed_response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(borrowed_response.data['book'], book_response.data['id'])
		book_detail_url = f'{self.list_url}{book_response.data["id"]}/'
		book_after_borrow = self.client.get(book_detail_url)
		self.assertFalse(book_after_borrow.data['is_available'])
		self.assertEqual(self.client.get(self.available_url).data['count'], 0)
		self.assertEqual(self.client.get(self.borrowed_book_list_url).data[0]['id'], borrowed_response.data['id'])

		second_borrow_response = self.client.post(
			self.borrowed_book_list_url,
			{
				'book': book_response.data['id'],
				'borrower_name': 'Another Reader',
			},
			format='json',
		)
		self.assertEqual(second_borrow_response.status_code, status.HTTP_400_BAD_REQUEST)
		borrowed_detail_url = (
			f'{self.borrowed_book_list_url}{borrowed_response.data["id"]}/'
		)

		borrowed_detail_response = self.client.get(borrowed_detail_url)
		self.assertEqual(borrowed_detail_response.status_code, status.HTTP_200_OK)

		borrowed_update_response = self.client.patch(
			borrowed_detail_url,
			{'borrower_name': 'Alex Updated'},
			format='json',
		)
		self.assertEqual(borrowed_update_response.status_code, status.HTTP_200_OK)

		borrowed_delete_response = self.client.delete(borrowed_detail_url)
		self.assertEqual(borrowed_delete_response.status_code, status.HTTP_409_CONFLICT)

		return_response = self.client.post(f'{borrowed_detail_url}return/')
		self.assertEqual(return_response.status_code, status.HTTP_200_OK)
		self.assertIsNotNone(return_response.data['returned_at'])

		book_after_return = self.client.get(book_detail_url)
		self.assertTrue(book_after_return.data['is_available'])
		self.assertEqual(self.client.get(self.borrowed_book_list_url).data, [])
		available_books = self.client.get(self.available_url)
		self.assertEqual(available_books.data['count'], 1)
		self.assertEqual(available_books.data['results'][0]['id'], book_response.data['id'])

		second_return_response = self.client.post(f'{borrowed_detail_url}return/')
		self.assertEqual(second_return_response.status_code, status.HTTP_409_CONFLICT)

		borrowed_delete_response = self.client.delete(borrowed_detail_url)
		self.assertEqual(borrowed_delete_response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertEqual(BorrowedBook.objects.count(), 0)

	def test_filter_by_title_and_category(self):
		matching_book = self.create_book('The Hobbit')
		self.create_book('The Silmarillion', category='Fantasy')
		self.create_book('A Brief History', category='History')

		response = self.client.get(self.list_url, {'title': 'hob', 'category': 'fiction'})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual([book['id'] for book in response.data['results']], [matching_book.id])

	def test_search_and_sort(self):
		zulu = self.create_book('Zulu', description='A history book.')
		alpha = self.create_book('Alpha')

		response = self.client.get(self.list_url, {'search': 'history', 'ordering': 'title'})
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual([book['id'] for book in response.data['results']], [zulu.id])

		response = self.client.get(self.list_url, {'ordering': 'title'})
		self.assertEqual(
			[book['id'] for book in response.data['results']],
			[alpha.id, zulu.id],
		)

	def test_list_paginates_five_books_per_page(self):
		for number in range(7):
			self.create_book(f'Book {number:02d}')

		first_page = self.client.get(self.list_url)
		second_page = self.client.get(self.list_url, {'page': 2})

		self.assertEqual(first_page.status_code, status.HTTP_200_OK)
		self.assertEqual(first_page.data['count'], 7)
		self.assertEqual(len(first_page.data['results']), 5)
		self.assertIsNotNone(first_page.data['next'])
		self.assertEqual(len(second_page.data['results']), 2)
		self.assertIsNone(second_page.data['next'])
