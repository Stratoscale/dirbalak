from twisted.web import resource
from twisted.web import server
import simplejson
from twisted.internet import reactor
import sys


class Event(resource.Resource):
    def render_POST(self, request):
        data = simplejson.loads(request.content.getvalue())
        repo = data['repository']['url']
        try:
            sys.stdout.write(repo + "\n")
            sys.stdout.flush()
        except:
            reactor.stop()
            raise
        return 'okeydokey'


def main(port):
    root = resource.Resource()
    root.putChild("event", Event())
    reactor.listenTCP(port, server.Site(root))
    reactor.run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=60004)
    args = parser.parse_args()
    main(args.port)
