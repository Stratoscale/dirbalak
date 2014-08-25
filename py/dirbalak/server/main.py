from realtimewebui import server
from realtimewebui import rootresource
from realtimewebui import render
import argparse
from dirbalak.server import fetchthread
from dirbalak.server import multiverse
from dirbalak.server import resources
from dirbalak.server import graphsresource
from dirbalak.server import callbacks
from dirbalak.rackrun import queue
from dirbalak.server import scriptologresource
from dirbalak.rackrun import pool
from dirbalak.rackrun import config
from twisted.web import static
import logging
import signal
import sys
import subprocess
import atexit


def _exit(*args):
    sys.exit()

signal.signal(signal.SIGTERM, _exit)
signal.signal(signal.SIGINT, _exit)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser()
parser.add_argument("--webPort", type=int, default=6001)
parser.add_argument("--webSocketPort", type=int, default=6002)
parser.add_argument("--logbeamWebFrontendPort", type=int, default=6003)
parser.add_argument("--githubListenerPort", type=int, default=6004)
parser.add_argument("--username", default="stratotest")
parser.add_argument("--password", default="2good2betruebettercallchucknorris")
parser.add_argument("--multiverseFile", required=True)
parser.add_argument("--officialObjectStore", required=True)
parser.add_argument("--unsecured", action="store_true")
parser.add_argument("--githubNetRCFile", required=True)
args = parser.parse_args()

config.GITHUB_NETRC_FILE = args.githubNetRCFile

logbeamWebFrontend = subprocess.Popen([
    "logbeam", 'webfrontend', "--port", str(args.logbeamWebFrontendPort),
    "--basicAuthUser", args.username, "--basicAuthPassword", args.password])
atexit.register(lambda *a: logbeamWebFrontend.terminate())

fetchThread = fetchthread.FetchThread()
multiverseInstance = multiverse.Multiverse.load(args.multiverseFile, fetchThread=fetchThread)
multiverseInstance.needsFetch("Dirbalak starting")
fetchThread.start(multiverseInstance)
callbacks.Callbacks(multiverseInstance)
queueInstance = queue.Queue(args.officialObjectStore, multiverseInstance)
fetchThread.addPostTraverseCallback(queueInstance.recalculate)
pool.Pool(queueInstance)

render.addTemplateDir("html")
render.DEFAULTS['title'] = "Dirbalak"
render.DEFAULTS['brand'] = "Dirbalak"
render.DEFAULTS['mainMenu'] = [
    dict(title="Projects", href="/projects"),
    dict(title="Queue", href="/queue"),
    dict(title="Build Hosts", href="/buildHosts")]
root = rootresource.rootResource()
root.putChild("js", static.File("js"))
rootresource.GLOBAL_PARAMETERS['logbeamWebFrontendPort'] = args.logbeamWebFrontendPort
root.putChild("projects", rootresource.Renderer("projects.html", dict(activeMenuItem="Projects")))
root.putChild("queue", rootresource.Renderer("queue.html", dict(activeMenuItem="Queue")))
root.putChild("buildHosts", rootresource.Renderer("buildHosts.html", dict(activeMenuItem="Build Hosts")))
root.putChild("project", resources.Projects())
root.putChild("scriptolog", scriptologresource.ScriptologResource(multiverseInstance))
graphResource = graphsresource.GraphsResource(multiverseInstance)
root.putChild("graphs", graphResource)
fetchThread.addPostTraverseCallback(graphResource.update)
if args.unsecured:
    server.runUnsecured(root, args.webPort, args.webSocketPort)
else:
    server.runSecured(root, args.webPort, args.webSocketPort, args.username, args.password)
