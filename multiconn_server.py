import selectors, socket, sys, types


sel = selectors.DefaultSelector()




def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f'Accepted connection from {addr}')
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')          # Object to hold data we want included along with sockets.
    events = selectors.EVENT_READ | selectors.EVENT_WRITE               # Know when client connection is ready for r/w
    sel.register(conn, events, data=data)


# Handling a client connection
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:                                                           # Client has closed connection, so should server
            print(f'closing connection to {data.addr}')
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f'echoing {repr(data.outb)} to {data.addr}')
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]                                # any received data stored in data.outb is echoed to the client using sock.send()



# while True:
#     events = sel.select(timeout=None)                # blocks until there are sockets ready for I/O. It returns a list of (key, events)tuples, one for each socket.
#     for key, mask in events:                         # key - SelectorKey namedtuple with fileobj attrib key. mask - event mask of the operations that are ready.
#         if key.data is None:
#             accept_wrapper(key.fileobj)              # Get new socket object and register it with selector
#         else:
#             service_connection(key, mask)            # service the client socket passing key and mask


if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))

# Configure socket in non-blocking mode
lsock.setblocking(False)
# Register socket to be monitored by sel.select() for read event.
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()


