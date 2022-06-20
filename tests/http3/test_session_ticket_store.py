from datetime import datetime

from aioquic.tls import CipherSuite, SessionTicket

from sanic.http.http3 import SessionTicketStore


def _generate_ticket(label):
    return SessionTicket(
        1,
        CipherSuite.AES_128_GCM_SHA256,
        datetime.now(),
        datetime.now(),
        label,
        label.decode(),
        label,
        None,
        [],
    )


def test_session_ticket_store():
    store = SessionTicketStore()

    assert len(store.tickets) == 0

    ticket1 = _generate_ticket(b"foo")
    store.add(ticket1)

    assert len(store.tickets) == 1

    ticket2 = _generate_ticket(b"bar")
    store.add(ticket2)

    assert len(store.tickets) == 2
    assert len(store.tickets) == 2

    popped2 = store.pop(ticket2.ticket)

    assert len(store.tickets) == 1
    assert popped2 is ticket2

    popped1 = store.pop(ticket1.ticket)

    assert len(store.tickets) == 0
    assert popped1 is ticket1
