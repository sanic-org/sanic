from aiofiles.os import stat
from os import path
from re import sub
from time import strftime, gmtime
from urllib.parse import unquote

from .exceptions import FileNotFound, InvalidUsage
from .response import file, HTTPResponse


def register(app, uri, file_or_directory, pattern, use_modified_since):
    # TODO: Though sanic is not a file server, I feel like we should atleast
    #       make a good effort here.  Modified-since is nice, but we could
    #       also look into etags, expires, and caching
    """
    Registers a static directory handler with Sanic by adding a route to the
    router and registering a handler.
    :param app: Sanic
    :param file_or_directory: File or directory path to serve from
    :param uri: URL to serve from
    :param pattern: regular expression used to match files in the URL
    :param use_modified_since: If true, send file modified time, and return
                     not modified if the browser's matches the server's
    """

    # If we're not trying to match a file directly,
    # serve from the folder
    if not path.isfile(file_or_directory):
        uri += '<file_uri:' + pattern + '>'

    async def _handler(request, file_uri=None):
        # Using this to determine if the URL is trying to break out of the path
        # served.  os.path.realpath seems to be very slow
        if file_uri and '../' in file_uri:
            raise InvalidUsage("Invalid URL")
        # Merge served directory and requested file if provided
        # Strip all / that in the beginning of the URL to help prevent python
        # from herping a derp and treating the uri as an absolute path
        file_path = file_or_directory
        if file_uri:
            file_path = path.join(
                file_or_directory, sub('^[/]*', '', file_uri))

        # URL decode the path sent by the browser otherwise we won't be able to
        # match filenames which got encoded (filenames with spaces etc)
        file_path = unquote(file_path)
        try:
            headers = {}
            # Check if the client has been sent this file before
            # and it has not been modified since
            if use_modified_since:
                stats = await stat(file_path)
                modified_since = strftime('%a, %d %b %Y %H:%M:%S GMT',
                                          gmtime(stats.st_mtime))
                if request.headers.get('If-Modified-Since') == modified_since:
                    return HTTPResponse(status=304)
                headers['Last-Modified'] = modified_since

            return await file(file_path, headers=headers)
        except:
            raise FileNotFound('File not found',
                               path=file_or_directory,
                               relative_url=file_uri)

    app.route(uri, methods=['GET'])(_handler)
