from realtimewebui import model
import time


class Model(model.Model):
    MAXIMUM_EVENTS_BACKLOG = 50

    def appendEvent(self, eventListID, text):
        events = self.get("events/%s" % eventListID)
        if events is None:
            events = []
        events.append(dict(time=time.time(), text=text))
        events = events[- self.MAXIMUM_EVENTS_BACKLOG: ]
        self.set("events/%s" % eventListID, events)

    def addToProjectsList(self, asDict):
        projectsList = self.get("projectsList")
        if projectsList is None:
            projectsList = []
        urls = [p['gitURL'] for p in projectsList]
        if asDict['gitURL'] not in urls:
            self.set("projectsList", projectsList + [asDict])
