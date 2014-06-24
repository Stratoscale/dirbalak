import argparse
from dirbalak import discover
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
discoverCmd.add_argument("--graphicOutput", help="use dot to discover the output")
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
else:
    assert False, "command mismatch"
