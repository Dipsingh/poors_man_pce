import zmq,os,string,time
from multiprocessing import Process
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

xpub_url = "tcp://127.0.0.1:50001"
xsub_url = "tcp://127.0.0.1:50002"

def broker():
    ctx =zmq.Context()
    xpub=ctx.socket(zmq.XPUB)
    xpub.bind(xpub_url)
    xsub=ctx.socket(zmq.XSUB)
    xsub.bind(xsub_url)
    poller = zmq.Poller()
    poller.register(xpub,zmq.POLLIN)
    poller.register(xsub,zmq.POLLIN)
    print ("Starting broker While Loop")
    zmq.proxy(xsub,xpub)

    while True:
        socks = dict(poller.poll())
        print ("Socks are",socks)
        if socks.get(xpub) == zmq.POLLIN:
            message = xpub.recv_json()
            print ("[BROKER] subscription PUB message: %r" %message)
            xsub.send_json(message)
        if socks.get(xsub) == zmq.POLLIN:
            message = xsub.recv_json()
            print ("[BROKER Subscription SUB message: ]", message)
            xpub.send_json(message)



def broker_main():
    broker()


if __name__ == '__main__':
    main()