import logging
import argparse
import realtimewebui.config
from dirbalak.rackrun import config


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser()
parser.add_argument("--webPort", type=int, default=6001)
parser.add_argument("--webSocketPort", type=int, default=6002)
parser.add_argument("--logbeamWebFrontendPort", type=int, default=6003)
parser.add_argument("--githubListenerPort", type=int)
parser.add_argument("--username", default="stratotest")
parser.add_argument("--password", default="2good2betruebettercallchucknorris")
parser.add_argument("--multiverseFile", required=True)
parser.add_argument("--officialObjectStore", required=True)
parser.add_argument("--unsecured", action="store_true")
parser.add_argument("--githubNetRCFile", required=True)
parser.add_argument("--realtimewebuiRoot")
parser.add_argument("--dirbalakRoot", default=".")
args = parser.parse_args()

config.GITHUB_NETRC_FILE = args.githubNetRCFile
if args.realtimewebuiRoot is not None:
    realtimewebui.config.REALTIMEWEBUI_ROOT_DIRECTORY = args.realtimewebuiRoot


from realtimewebui import server
from realtimewebui import rootresource
from realtimewebui import render
from dirbalak.server import fetchthread
from dirbalak.server import multiverse
from dirbalak.server import resources
from dirbalak.server import graphsresource
from dirbalak.server import callbacks
from dirbalak.server import spawngithubwebeventlistener
from dirbalak.rackrun import jobqueue
from dirbalak.server import scriptologresource
from dirbalak.rackrun import pool
from dirbalak import rackrun
from upseto import gitwrapper
from twisted.web import static
import logbeam.config
import subprocess
import atexit
import os
import signal


multiverseInstance = None


def fetchRepoFromWebHook(repo):
    global multiverseInstance
    if multiverseInstance is None:
        return
    basename = gitwrapper.originURLBasename(repo)
    if basename not in multiverseInstance.projects:
        logging.error("Webhook called for unfamiliar repo '%(repo)s'", dict(repo=repo))
        return
    project = multiverseInstance.projects[basename]
    project.needsFetch('Webhook triggered fetch')


if args.githubListenerPort is not None:
    spawngithubwebeventlistener.SpawnGithubWebEventListener(fetchRepoFromWebHook)
logbeam.config.load()
logbeamWebFrontend = subprocess.Popen([
    "logbeam", 'webfrontend', "--port", str(args.logbeamWebFrontendPort),
    "--basicAuthUser", args.username, "--basicAuthPassword", args.password])
atexit.register(lambda *a: logbeamWebFrontend.terminate())

fetchThread = fetchthread.FetchThread()
multiverseInstance = multiverse.Multiverse.load(args.multiverseFile, fetchThread=fetchThread)
fetchThread.start(multiverseInstance)
callbacks.Callbacks(multiverseInstance)
jobQueue = jobqueue.JobQueue(args.officialObjectStore, multiverseInstance)
fetchThread.addPostTraverseCallback(jobQueue.recalculate)
graphResource = graphsresource.GraphsResource(multiverseInstance)


def reloadConfig(*ignored):
    logging.info("Received SIGHUP, rereading multiverse file")
    multiverseInstance.rereadMultiverseFile(args.multiverseFile)
    jobQueue.recalculate()


signal.signal(signal.SIGHUP, reloadConfig)


def jobDone(job, successfull):
    project = multiverseInstance.projects[job['basename']]
    project.refreshMasterBuildHistory()
    graphResource.update()


pool.Pool(jobQueue, jobDoneCallback=jobDone)

rackrun.config.DIRBALAK_EGG_DIR = args.dirbalakRoot
render.addTemplateDir(os.path.join(args.dirbalakRoot, 'html'))
render.DEFAULTS['title'] = "Dirbalak"
render.DEFAULTS['brand'] = "Dirbalak"
render.DEFAULTS['mainMenu'] = [
    dict(title="Projects", href="/projects"),
    dict(title="Queue", href="/queue"),
    dict(title="Build Hosts", href="/buildHosts")]
root = rootresource.rootResource()
root.putChild("js", static.File(os.path.join(args.dirbalakRoot, "js")))
root.putChild("static", static.File(os.path.join(args.dirbalakRoot, "static")))
root.putChild("favicon.ico", static.File(os.path.join(args.dirbalakRoot, "static", "favicon.ico")))
rootresource.GLOBAL_PARAMETERS['logbeamWebFrontendPort'] = args.logbeamWebFrontendPort
root.putChild("projects", rootresource.Renderer("projects.html", dict(activeMenuItem="Projects")))
root.putChild("queue", rootresource.Renderer("queue.html", dict(activeMenuItem="Queue")))
root.putChild("buildHosts", rootresource.Renderer("buildHosts.html", dict(activeMenuItem="Build Hosts")))
root.putChild("project", resources.Projects())
root.putChild("scriptolog", scriptologresource.ScriptologResource(multiverseInstance))
root.putChild("graphs", graphResource)
fetchThread.addPostTraverseCallback(graphResource.update)
if args.unsecured:
    server.runUnsecured(root, args.webPort, args.webSocketPort)
else:
    server.runSecured(root, args.webPort, args.webSocketPort, args.username, args.password)
