import django.db.models.deletion
from django.db import migrations, models


def copy_existing_author_links(apps, schema_editor):
    database = schema_editor.connection.alias
    Book = apps.get_model('books_api', 'Book')
    Author = apps.get_model('books_api', 'Author')

    for author in Author.objects.using(database).exclude(book_id=None).order_by('id').iterator():
        Book.objects.using(database).filter(
            pk=author.book_id,
            author_id__isnull=True,
        ).update(author_id=author.pk)


def assign_unknown_author(apps, schema_editor):
    database = schema_editor.connection.alias
    Book = apps.get_model('books_api', 'Book')
    Author = apps.get_model('books_api', 'Author')
    books_without_authors = Book.objects.using(database).filter(author__isnull=True)

    if books_without_authors.exists():
        author = Author.objects.using(database).create(
            name='Unknown author',
            biography='Created during migration for books without an assigned author.',
        )
        books_without_authors.update(author_id=author.pk)


class Migration(migrations.Migration):

    dependencies = [
        ('books_api', '0002_author_borrowedbook'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='author',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='books',
                to='books_api.author',
            ),
        ),
        migrations.RunPython(copy_existing_author_links, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='author',
            name='book',
        ),
        migrations.RunPython(assign_unknown_author, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='book',
            name='author',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='books',
                to='books_api.author',
            ),
        ),
    ]