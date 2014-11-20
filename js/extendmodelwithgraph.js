function extendModelWithGraph(model, source)
{
    var self = model;

    self.dirbalakBuildRootFSArcs = ko.observable(false);
    self.solventRootFSArcs = ko.observable(true);

    self._imageSourceDirectory = source;
    self._imageSource = function() {
        return self._imageSourceDirectory + "/image" +
                "?dirbalakBuildRootFSArcs=" + (self.dirbalakBuildRootFSArcs()?"yes":"") +
                "&solventRootFSArcs=" + (self.solventRootFSArcs()?"yes":"") +
                "&avoidBrowserCachingWithRandomString=" + self._makeUpRandomString();
    };

    self.updateGraph = function() {
        console.log("Updating graph");
       $.get(self._imageSource(), undefined, function(svgDoc) {
            var svgDocElement = svgDoc.documentElement;
            document.adoptNode(svgDocElement);
            $("#graph").html(svgDocElement);
        })
    }
    self.dirbalakBuildRootFSArcs.subscribe(self.updateGraph);
    self.solventRootFSArcs.subscribe(self.updateGraph);

    self._makeUpRandomString = function() {
        var text = "";
        var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

        for(var i=0; i<32; i++)
            text += possible.charAt(Math.floor(Math.random() * possible.length));

        return text;
    }

    self.updateGraph();
}
