from asyncorm.model import ModelSerializer, SerializerMethod
from library.models import Book


class BookSerializer(ModelSerializer):
    book_type = SerializerMethod()

    def get_book_type(self, instance):
        return instance.book_type_display()

    class Meta():
        model = Book
        fields = [
            'id', 'name', 'synopsis', 'book_type', 'pages', 'date_created'
        ]
