from multiprocessing.connection import Client
from array import array

address = ('localhost', 3005)

with Client(address, authkey=b'secret password') as conn:
    print(conn.recv())                  # => [2.25, None, 'junk', float]
    print(conn.recv_bytes())            # => 'hello'