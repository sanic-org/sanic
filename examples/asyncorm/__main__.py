from sanic import Sanic
from sanic.exceptions import NotFound
from sanic.response import json
from sanic.views import HTTPMethodView

from asyncorm import configure_orm
from asyncorm.exceptions import QuerysetError

from library.models import Book
from library.serializer import BookSerializer

app = Sanic(name=__name__)


@app.listener('before_server_start')
def orm_configure(sanic, loop):
    db_config = {'database': 'sanic_example',
                 'host': 'localhost',
                 'user': 'sanicdbuser',
                 'password': 'sanicDbPass',
                 }

    # configure_orm needs a dictionary with:
    #    * the database configuration
    #    * the application/s where the models are defined
    orm_app = configure_orm({'loop': loop,  # always use the sanic loop!
                             'db_config': db_config,
                             'modules': ['library', ],  # list of apps
                             })

    # orm_app is the object that orchestrates the whole ORM
    # sync_db should be run only once, better do that as external command
    # it creates the tables in the database!!!!
    # orm_app.sync_db()


# for all the 404 lets handle the exceptions
@app.exception(NotFound)
def ignore_404s(request, exception):
    return json({'method': request.method,
                 'status': exception.status_code,
                 'error': exception.args[0],
                 'results': None,
                 })


# now the propper sanic workflow
class BooksView(HTTPMethodView):
    def arg_parser(self, request):
        parsed_args = {}
        for k, v in request.args.items():
            parsed_args[k] = v[0]
        return parsed_args

    async def get(self, request):
        filtered_by = self.arg_parser(request)

        if filtered_by:
            q_books = await Book.objects.filter(**filtered_by)
        else:
            q_books = await Book.objects.all()

        books = [BookSerializer.serialize(book) for book in q_books]

        return json({'method': request.method,
                     'status': 200,
                     'results': books or None,
                     'count': len(books),
                     })

    async def post(self, request):
        # populate the book with the data in the request
        book = Book(**request.json)

        # and await on save
        await book.save()

        return json({'method': request.method,
                     'status': 201,
                     'results': BookSerializer.serialize(book),
                     })


class BookView(HTTPMethodView):
    async def get_object(self, request, book_id):
        try:
            # await on database consults
            book = await Book.objects.get(**{'id': book_id})
        except QuerysetError as e:
            raise NotFound(e.args[0])
        return book

    async def get(self, request, book_id):
        # await on database consults
        book = await self.get_object(request, book_id)

        return json({'method': request.method,
                     'status': 200,
                     'results': BookSerializer.serialize(book),
                     })

    async def put(self, request, book_id):
        # await on database consults
        book = await self.get_object(request, book_id)
        # await on save
        await book.save(**request.json)

        return json({'method': request.method,
                     'status': 200,
                     'results': BookSerializer.serialize(book),
                     })

    async def patch(self, request, book_id):
        # await on database consults
        book = await self.get_object(request, book_id)
        # await on save
        await book.save(**request.json)

        return json({'method': request.method,
                     'status': 200,
                     'results': BookSerializer.serialize(book),
                     })

    async def delete(self, request, book_id):
        # await on database consults
        book = await self.get_object(request, book_id)
        # await on its deletion
        await book.delete()

        return json({'method': request.method,
                     'status': 200,
                     'results': None
                     })


app.add_route(BooksView.as_view(), '/books/')
app.add_route(BookView.as_view(), '/books/<book_id:int>/')

if __name__ == '__main__':
    app.run()
