from asyncorm.model import Model
from asyncorm.fields import CharField, IntegerField, DateField


BOOK_CHOICES = (
    ('hard cover', 'hard cover book'),
    ('paperback', 'paperback book')
)


# This is a simple model definition
class Book(Model):
    name = CharField(max_length=50)
    synopsis = CharField(max_length=255)
    book_type = CharField(max_length=15, null=True, choices=BOOK_CHOICES)
    pages = IntegerField(null=True)
    date_created = DateField(auto_now=True)

    class Meta():
        ordering = ['name', ]
        unique_together = ['name', 'synopsis']
