import argparse
from dirbalak import discover
from dirbalak import config
from dirbalak import repomirrorcache
from upseto import gitwrapper
from upseto import run
import logging
import os

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
discoverCmd.add_argument("--graphicOutput", help="use dot to discover the output")
cleanbuildCmd = subparsers.add_parser(
    "cleanbuild",
    help="cleanly build a project")
whatGroup = cleanbuildCmd.add_mutually_exclusive_group(required=True)
whatGroup.add_argument("--gitURL")
whatGroup.add_argument("--currentProject", action='store_true')
cleanbuildCmd.add_argument("--hash", default="origin/master")
args = parser.parse_args()

if args.cmd == "discover":
    projects = list(args.gitURL)
    if args.currentProject:
        projects.append(gitwrapper.GitWrapper('.').originURL())
    if len(projects) == 0:
        raise Exception("No projects specified in command line")
    discoverInstance = discover.Discover(projects)
    print discoverInstance.renderText()
    if args.graphicOutput:
        discoverInstance.saveGraphPng(args.graphicOutput)
elif args.cmd == "cleanbuild":
    os.environ['SOLVENT_CLEAN'] = 'Yes'
    buildRootFSlabel = config.DEFAULT_BUILD_ROOTFS_LABEL
    logging.info("checking out build chroot at label '%(label)s'", dict(label=buildRootFSlabel))
    run.run([
        "sudo", "solvent", "bringlabel", "--label", buildRootFSlabel,
        "--destination", config.BUILD_CHROOT])
    gitURL = gitwrapper.GitWrapper(".").originURL() if args.currentProject else args.gitURL
    mirror = repomirrorcache.get(gitURL)
    assert len(mirror.upsetoManifest(args.hash).requirements()) == 0
    assert len(mirror.solventManifest(args.hash).requirements()) == 0
    logging.info("Creating git repo inside chroot")
    mirror.replicate(config.BUILD_DIRECTORY)
    git = gitwrapper.GitWrapper.existing(gitURL, config.BUILD_DIRECTORY)
    git.checkout(args.hash)
    relative = git.directory()[len(config.BUILD_CHROOT):]
    logging.info("Running make")
    run.run([
        "sudo", "chroot", config.BUILD_CHROOT, "sh", "-c",
        "cd %s; make" % relative])
    run.run(["sudo", "-E", "solvent", "submitbuild"], cwd=git.directory())
    run.run(["sudo", "-E", "solvent", "approve"], cwd=git.directory())
else:
    assert False, "command mismatch"
