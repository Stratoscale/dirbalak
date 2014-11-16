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
    self._updateMap = function() {
        url = self._imageSourceDirectory + "/map" +
                "?dirbalakBuildRootFSArcs=" + (self.dirbalakBuildRootFSArcs()?"yes":"") +
                "&solventRootFSArcs=" + (self.solventRootFSArcs()?"yes":"") +
                "&avoidBrowserCachingWithRandomString=" + self._makeUpRandomString();
        $.ajax({url: url}).done(function(data) {
            $("#mainmap").html(data);
        });
    };

    self.updateGraph = function() {
        console.log("Updating graph");
        $("#graph").html('<img src="' + self._imageSource() + '" usemap="#mainmap"/>' + 
                        '<map id="mainmap" name="mainmap"></map>');
        self._updateMap();
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
