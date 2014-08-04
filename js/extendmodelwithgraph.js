function extendModelWithGraph(model, source)
{
    var self = model;

    self.dirbalakBuildRootFSArcs = ko.observable(false);
    self.solventRootFSArcs = ko.observable(true);

    self._imageSourceDirectory = source;
    self._imageSource = function() {
        return self._imageSourceDirectory + "/image" +
                "?dirbalakBuildRootFSArcs=" + (self.dirbalakBuildRootFSArcs()?"yes":"") +
                "&solventRootFSArcs=" + (self.solventRootFSArcs()?"yes":"");
    };
    self._updateMap = function() {
        url = self._imageSourceDirectory + "/map" +
                "?dirbalakBuildRootFSArcs=" + (self.dirbalakBuildRootFSArcs()?"yes":"") +
                "&solventRootFSArcs=" + (self.solventRootFSArcs()?"yes":"");
        $.ajax({url: url}).done(function(data) {
            $("#mainmap").html(data);
        });
    };

    self.updateGraph = function() {
        $("#graph").html('<img src="' + self._imageSource() + '" usemap="#mainmap"/>' + 
                        '<map id="mainmap" name="mainmap"></map>');
        self._updateMap();
    }
    self.dirbalakBuildRootFSArcs.subscribe(self.updateGraph);
    self.solventRootFSArcs.subscribe(self.updateGraph);
    self.updateGraph();
}
