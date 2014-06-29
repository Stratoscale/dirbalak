import argparse
from dirbalak import discover
from dirbalak import cleanbuild
from dirbalak import setoperation
from dirbalak import repomirrorcache
from upseto import gitwrapper
import logging

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="cmd")
discoverCmd = subparsers.add_parser(
    "discover",
    help="Discover the inter-repository dependencies")
discoverCmd.add_argument(
    "--currentProject", action='store_true',
    help="Add the current git project origin url to the project list to start discovery from")
discoverCmd.add_argument("--gitURL", nargs="*", help="Add this url to the discovery project list")
discoverCmd.add_argument("--graphicOutput", help="use dot to plot the output")
discoverCmd.add_argument("--dotOutput", help="save dot file")
discoverCmd.add_argument(
    "--noFetch", action="store_true",
    help="dont git fetch anything, use already fetched data only")
discoverCmd.add_argument(
    "--officialObjectStore",
    help="object store to test existance of labels in, to determine if built")
cleanbuildCmd = subparsers.add_parser(
    "cleanbuild",
    help="cleanly build a project")
whatGroup = cleanbuildCmd.add_mutually_exclusive_group(required=True)
whatGroup.add_argument("--gitURL")
whatGroup.add_argument("--currentProject", action='store_true')
cleanbuildCmd.add_argument("--hash", default="origin/master")
cleanbuildCmd.add_argument("--nosubmit", action="store_true")
setCmd = subparsers.add_parser(
    "set",
    help="set dirbalak parameters")
setCmd.add_argument(
    "key", help="one of: "
    "'buildRootFS' (==solvent requirement basename for rootfs product to build cleanly inside)")
setCmd.add_argument("value")
args = parser.parse_args()

if args.cmd == "discover":
    projects = list(args.gitURL)
    if args.currentProject:
        projects.append(gitwrapper.GitWrapper('.').originURL())
    if len(projects) == 0:
        raise Exception("No projects specified in command line")
    if args.noFetch:
        repomirrorcache.fetch = False
    discoverInstance = discover.Discover(projects, objectStore=args.officialObjectStore)
    print discoverInstance.renderText()
    if args.graphicOutput:
        graph = discoverInstance.makeGraph()
        graph.savePng(args.graphicOutput)
        logging.info("Saved '%(graphicOutput)s'", dict(graphicOutput=args.graphicOutput))
    if args.dotOutput:
        graph = discoverInstance.makeGraph()
        graph.saveDot(args.dotOutput)
elif args.cmd == "cleanbuild":
    gitURL = gitwrapper.GitWrapper(".").originURL() if args.currentProject else args.gitURL
    cleanbuild.CleanBuild(gitURL=gitURL, hash=args.hash, submit=not args.nosubmit).go()
elif args.cmd == "set":
    setoperation.SetOperation(key=args.key, value=args.value).go()
else:
    assert False, "command mismatch"
