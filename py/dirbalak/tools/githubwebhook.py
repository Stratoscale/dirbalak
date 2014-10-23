import argparse
import requests
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--username", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--organization", default="Stratoscale")
subparsers = parser.add_subparsers(dest="cmd")
listCmd = subparsers.add_parser("list", help="list configured webhooks")
interactiveAddCmd = subparsers.add_parser("addInteractive", help="add the hook interactively")
interactiveAddCmd.add_argument("--hook", required=True)
args = parser.parse_args()


def getProjects():
    result = []
    for i in xrange(1, 100):
        response = requests.get(
            'https://api.github.com/orgs/%s/repos' % args.organization,
            params=dict(per_page=100, page=i),
            auth=(args.username, args.password)).json()
        if len(response) == 0:
            return result
        result += response


def getProjectHooks(project):
    response = requests.get(project[u'hooks_url'], auth=(args.username, args.password)).json()
    return response


def addHook(project, hook):
    POST = \
        '{"name": "web", "active": true, "events": [ "push" ], ' \
        '"config": { "url": "%s", "content_type": "json" } }' % hook
    requests.post(project[u'hooks_url'], auth=(args.username, args.password), data=POST)

if args.cmd == "list":
    projects = getProjects()
    print "Projects:", len(projects)
    for project in projects:
        print project[u'name']
        for hook in getProjectHooks(project):
            print "\t", hook[u'config'][u'url']
elif args.cmd == "addInteractive":
    projects = getProjects()
    print "Projects:", len(projects)
    for project in reversed(projects):
        hasHook = False
        for hook in getProjectHooks(project):
            if hook[u'config'][u'url'] == args.hook:
                hasHook = True
        if hasHook:
            print project[u'name'], "Already has the hook"
        else:
            print project[u'name'], "Doesn't have the hook, should i add? [y/N]"
            line = sys.stdin.readline().strip().lower()
            if line == "yes" or line == "y":
                addHook(project, args.hook)
                print project[u'name'], "Added hook"
            else:
                print project[u'name'], "Did not add hook"
