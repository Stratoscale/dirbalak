function extendModelWithGraph(model, source)
{
    var self = model;

    self.REFRESH_INTERVAL = 60 * 1000;

    self.dirbalakBuildRootFSArcs = ko.observable(false);
    self.solventRootFSArcs = ko.observable(true);
    self.newGraphVersionAvailable = ko.observable(false);
    self.lastUpdate = new Date(0);

    self._imageSourceDirectory = source;
    self._imageSource = function() {
        return self._imageSourceDirectory + "/image" +
                "?dirbalakBuildRootFSArcs=" + (self.dirbalakBuildRootFSArcs()?"yes":"") +
                "&solventRootFSArcs=" + (self.solventRootFSArcs()?"yes":"") +
                "&avoidBrowserCachingWithRandomString=" + self._makeUpRandomString();
    };

    self.updateGraph = function() {
        console.log("Updating graph");
        self.newGraphVersionAvailable(false);
        self.lastUpdate = new Date();
        $.get(self._imageSource(), undefined, function(svgDoc) {
            var svgDocElement = svgDoc.documentElement;
            document.adoptNode(svgDocElement);
            $("#graph").html(svgDocElement);
        })
    };
    self.dirbalakBuildRootFSArcs.subscribe(self.updateGraph);
    self.solventRootFSArcs.subscribe(self.updateGraph);

    self.forceGraphUpdate = function() {
        self.updateGraph();
    };

    self._makeUpRandomString = function() {
        var text = "";
        var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

        for(var i=0; i<32; i++)
            text += possible.charAt(Math.floor(Math.random() * possible.length));

        return text;
    };

    self.updateGraph();

    self.newVersionOfGraphAvailable = function() {
        console.log("New version of graph available");
        var fromLastUpdate = (new Date()).getTime() - self.lastUpdate.getTime();
        if (fromLastUpdate >= self.REFRESH_INTERVAL) {
            self.updateGraph();
            return;
        }
        self.newGraphVersionAvailable(true);
        setTimeout(function() {
            var fromLastUpdate = (new Date()).getTime() - self.lastUpdate.getTime();
            if (fromLastUpdate >= self.REFRESH_INTERVAL)
                self.updateGraph();
        }, self.REFRESH_INTERVAL - fromLastUpdate + 100);
    };
}
