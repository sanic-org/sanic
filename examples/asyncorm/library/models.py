from asyncorm import models


BOOK_CHOICES = (
    ('hard cover', 'hard cover book'),
    ('paperback', 'paperback book')
)


# This is a simple model definition
class Book(models.Model):
    name = models.CharField(max_length=50)
    synopsis = models.CharField(max_length=255)
    book_type = models.CharField(
        max_length=15,
        null=True,
        choices=BOOK_CHOICES
    )
    pages = models.IntegerField(null=True)
    date_created = models.DateField(auto_now=True)

    class Meta():
        ordering = ['-name', ]
        unique_together = ['name', 'synopsis']
