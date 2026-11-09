from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books_api', '0004_book_is_available'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='is_available',
        ),
    ]