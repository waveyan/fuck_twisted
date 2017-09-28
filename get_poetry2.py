# This is the Twisted Get Poetry Now! client, version 2.0.

# NOTE: This should not be used as the basis for production code.

import datetime, optparse

from twisted.internet.protocol import Protocol, ClientFactory


def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 2.0.
Run it like this:

  python get-poetry.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-2/get-poetry.py 10001 10002 10003

to grab poetry from servers on ports 10001, 10002, and 10003.

Of course, there need to be servers listening on those ports
for that to work.
"""

    parser = optparse.OptionParser(usage)

    _, addresses = parser.parse_args()

    if not addresses:
        print(parser.format_help())
        parser.exit()

    def parse_address(addr):
        if ':' not in addr:
            host = '127.0.0.1'
            port = addr
        else:
            host, port = addr.split(':', 1)

        if not port.isdigit():
            parser.error('Ports must be integers.')

        return host, int(port)

    return list(map(parse_address, addresses))

#一个Protocol对应一个transport，transport看作一个分身，protocol告诉这个分身怎么做
class PoetryProtocol(Protocol):

    poem = ''
    task_num = 0

    #分身接收数据的规则
    def dataReceived(self, data):
        self.poem += data.decode('utf8')
        msg = 'Task %d: got %d bytes of poetry from %s'
        print(msg % (self.task_num, len(data), self.transport.getPeer()))

    #分身接受完成时调用
    def connectionLost(self, reason):
        self.poemReceived(self.poem)

    def poemReceived(self, poem):
        self.factory.poem_finished(self.task_num, poem)


class PoetryClientFactory(ClientFactory):

    task_num = 1

    #为该ClientFactory创建的分身transport指明一个Protocol
    protocol = PoetryProtocol # tell base class what proto to build

    def __init__(self, poetry_count):
        self.poetry_count = poetry_count
        self.poems = {} # task num -> poem

    #建立分身transport时调用，建立transport和protocol的关系
    def buildProtocol(self, address):
        proto = ClientFactory.buildProtocol(self, address)
        proto.task_num = self.task_num
        self.task_num += 1
        return proto

    #全部分身transport做完工作后被调用
    def poem_finished(self, task_num=None, poem=None):
        if task_num is not None:
            self.poems[task_num] = poem

        self.poetry_count -= 1

        if self.poetry_count == 0:
            self.report()
            from twisted.internet import reactor
            reactor.stop()

    def report(self):
        for i in self.poems:
            print('Task %d: %d bytes of poetry' % (i, len(self.poems[i])))

    #某个分身连接失败时被调用
    def clientConnectionFailed(self, connector, reason):
        print('Failed to connect to:', connector.getDestination())
        self.poem_finished()


def poetry_main():
    addresses = parse_args()

    start = datetime.datetime.now()

    #建立一个制造分身的工厂
    factory = PoetryClientFactory(len(addresses))

    from twisted.internet import reactor

    #通过循环创造多个分身
    for address in addresses:
        host, port = address
        reactor.connectTCP(host, port, factory)


    reactor.run()

    elapsed = datetime.datetime.now() - start

    print('Got %d poems in %s' % (len(addresses), elapsed))


if __name__ == '__main__':
    poetry_main()

#分身transport可理解为一个对象实例