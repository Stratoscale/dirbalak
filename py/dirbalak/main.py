import argparse
from dirbalak import describe
from dirbalak import discover
from dirbalak import cleanbuild
from dirbalak import setoperation
from dirbalak import repomirrorcache
from dirbalak import unreferencedlabels
from dirbalak import traverse
from dirbalak import scriptolog
from upseto import gitwrapper
import logging
import yaml

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="cmd")
describeCmd = subparsers.add_parser(
    "describe",
    help="Describe the exact hashes of a single project/hash")
describeCmd.add_argument("--gitURL", required=True)
describeCmd.add_argument("--hash", required=True)
describeCmd.add_argument(
    "--noFetch", action="store_true",
    help="dont git fetch anything, use already fetched data only")
describeCmd.add_argument(
    "--noDirbalakBuildRootFSArcs", action="store_true",
    help="do not show solvent dependencies in the project dirbalak uses for clean build rootfs")
describeCmd.add_argument(
    "--noSolventRootFSArcs", action="store_true",
    help="do not show solvent dependencies in projects that starts with 'rootfs-'")
describeCmd.add_argument("--graphicOutput", help="use dot to plot the output")
describeCmd.add_argument("--dotOutput", help="save dot file")

discoverCmd = subparsers.add_parser(
    "discover",
    help="Discover the inter-repository dependencies")
discoverCmd.add_argument(
    "--currentProject", action='store_true',
    help="Add the current git project origin url to the project list to start discovery from")
discoverCmd.add_argument(
    "--gitURL", nargs="*", default=[], help="Add this url to the discovery project list")
discoverCmd.add_argument(
    "--multiverseFile",
    help="read multiverse file, will be used only for clustering, unless "
    "--projectsFromMultiverse is specified")
discoverCmd.add_argument(
    "--projectsFromMultiverse", action='store_true',
    help="use the project list in the multiverse file")
discoverCmd.add_argument("--graphicOutput", help="use dot to plot the output")
discoverCmd.add_argument("--dotOutput", help="save dot file")
discoverCmd.add_argument(
    "--noFetch", action="store_true",
    help="dont git fetch anything, use already fetched data only")
discoverCmd.add_argument(
    "--officialObjectStore",
    help="object store to test existance of labels in, to determine if built")
discoverCmd.add_argument(
    "--noDirbalakBuildRootFSArcs", action="store_true",
    help="do not show solvent dependencies in the project dirbalak uses for clean build rootfs")
discoverCmd.add_argument(
    "--noSolventRootFSArcs", action="store_true",
    help="do not show solvent dependencies in projects that starts with 'rootfs-'")

cleanbuildCmd = subparsers.add_parser(
    "cleanbuild",
    help="cleanly build a project")
whatGroup = cleanbuildCmd.add_mutually_exclusive_group(required=True)
whatGroup.add_argument("--gitURL")
whatGroup.add_argument("--currentProject", action='store_true')
cleanbuildCmd.add_argument("--hash", default="origin/master")
cleanbuildCmd.add_argument("--nosubmit", action="store_true")
cleanbuildCmd.add_argument(
    "--rootfs", help="label to build in. a dirbalak manifest should not exist "
    "to use this option")

setCmd = subparsers.add_parser(
    "set",
    help="set dirbalak parameters")
setCmd.add_argument(
    "key", help="one of: "
    "'buildRootFSRepositoryBasename' "
    "(==solvent requirement basename for rootfs product to build cleanly inside) "
    "'buildRootFSLabel' "
    "(==solvent label for to use as a rootfs to build cleanly inside. "
    "mutually exclusive with buildRootFSRepositoryBasename. Please do not use this but for "
    "bootstrapping rootfs projects)")
setCmd.add_argument("value")

unreferencedLabelsCmd = subparsers.add_parser(
    "unreferencedLabels", help="Find which labels are not referenced")
unreferencedLabelsCmd.add_argument("--multiverseFile", required=True)
unreferencedLabelsCmd.add_argument("--objectStore", required=True)
unreferencedLabelsCmd.add_argument(
    "--noFetch", action="store_true",
    help="dont git fetch anything, use already fetched data only")

scriptologCmd = subparsers.add_parser(
    "scriptolog",
    help="render a script")
scriptSubparser = scriptologCmd.add_subparsers(dest="script")
updateAllDependenciesScript = scriptSubparser.add_parser("updateAllDependencies")
updateAllDependenciesScript.add_argument("--gitURL")
args = parser.parse_args()

if getattr(args, 'noFetch', False):
    repomirrorcache.fetch = False

if args.cmd == 'describe':
    describeInstance = describe.Describe(
        gitURL=args.gitURL,
        hash=args.hash,
        dirbalakBuildRootFSArcs=not args.noDirbalakBuildRootFSArcs,
        solventRootFSArcs=not args.noSolventRootFSArcs)
    print describeInstance.renderText()
    if args.graphicOutput:
        graph = describeInstance.makeGraph()
        graph.saveSvg(args.graphicOutput)
        logging.info("Saved '%(graphicOutput)s'", dict(graphicOutput=args.graphicOutput))
    if args.dotOutput:
        graph = describeInstance.makeGraph()
        graph.saveDot(args.dotOutput)
elif args.cmd == "discover":
    projects = list(args.gitURL)
    if args.currentProject:
        projects.append(gitwrapper.GitWrapper('.').originURL())
    clusterMap = dict()
    if args.multiverseFile:
        with open(args.multiverseFile) as f:
            multiverse = yaml.load(f.read())
        clusterMap = {
            gitwrapper.originURLBasename(p['gitURL']): p['group'] for p in multiverse['PROJECTS']}
        if args.projectsFromMultiverse:
            projects += [p['gitURL'] for p in multiverse['PROJECTS']]
    if len(projects) == 0:
        raise Exception("No projects specified in command line")
    discoverInstance = discover.Discover(
        projects=projects, objectStore=args.officialObjectStore,
        clusterMap=clusterMap,
        dirbalakBuildRootFSArcs=not args.noDirbalakBuildRootFSArcs,
        solventRootFSArcs=not args.noSolventRootFSArcs)
    print discoverInstance.renderText()
    if args.graphicOutput:
        graph = discoverInstance.makeGraph()
        graph.saveSvg(args.graphicOutput)
        logging.info("Saved '%(graphicOutput)s'", dict(graphicOutput=args.graphicOutput))
    if args.dotOutput:
        graph = discoverInstance.makeGraph()
        graph.saveDot(args.dotOutput)
elif args.cmd == "cleanbuild":
    gitURL = gitwrapper.GitWrapper(".").originURL() if args.currentProject else args.gitURL
    cleanbuild.CleanBuild(
        gitURL=gitURL, hash=args.hash, submit=not args.nosubmit, buildRootFS=args.rootfs).go()
elif args.cmd == "set":
    setoperation.SetOperation(key=args.key, value=args.value).go()
elif args.cmd == "unreferencedLabels":
    with open(args.multiverseFile) as f:
        multiverse = yaml.load(f.read())
    instance = unreferencedlabels.UnreferencedLabels(
        projects=[p['gitURL'] for p in multiverse['PROJECTS']], objectStore=args.objectStore)
    for label in instance.unreferencedLabels():
        print label
elif args.cmd == "scriptolog":
    logging.getLogger().setLevel(logging.ERROR)
    if args.script == "updateAllDependencies":
        traverseInstance = traverse.Traverse()
        traverseInstance.traverse(args.gitURL, 'origin/master')
        print scriptolog.Scriptolog(traverseInstance).updateAllDependencies(args.gitURL)
    else:
        raise AssertionError("Unknown script")
else:
    assert False, "command mismatch"
