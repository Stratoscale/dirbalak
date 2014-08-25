var EventToHTML = new Object();

safeHTMLOfText = function(text)
{
    return $('<div/>').text(text).html();
}

EventToHTML._logbeamWebFrontendURL = function(path)
{
    var parts = window.location.href.split("/");
    var hostname = parts[2].split(":")[0];
    return "http://" + hostname + ":" + logbeamWebFrontendPort + path;
}

EventToHTML._hostAnchor = function(host)
{
    return '<a href="/buildHosts#' + host + '">Host ' + host + '</a>';
}

EventToHTML._jobAnchor = function(job)
{
    return 'Job <a href="/project/' + job.basename + '">' + job.basename + '</a> (' +
        job.hexHash + ')';
}

EventToHTML._buildAnchor = function(obj)
{
    return 'Build <a href="' + EventToHTML._logbeamWebFrontendURL("/dirbalak/" + obj.job.basename + "/" + obj.buildID) +
        '">' + obj.buildID + '</a>';
}

EventToHTML._green = function(text)
{
    return '<span style="color: #009933">' + text + '</span>';
}

EventToHTML._red = function(text)
{
    return '<span style="color: #CC0000">' + text + '</span>';
}

EventToHTML._renderObject = function(obj)
{
    if (obj.type == "text") {
        return safeHTMLOfText(obj.text);
    } else if (obj.type == 'job_started') {
        return EventToHTML._hostAnchor(obj.host) + " Started Building " + EventToHTML._jobAnchor(obj.job);
    } else if (obj.type == 'build_started') {
        return "Started " + EventToHTML._buildAnchor(obj) + " for " + EventToHTML._jobAnchor(obj.job);
    } else if (obj.type == 'build_failed') {
        return EventToHTML._red("Failed") + " " + EventToHTML._buildAnchor(obj) + " for " + EventToHTML._jobAnchor(obj.job);
    } else if (obj.type == 'build_succeeded') {
        return EventToHTML._green("Succeeded") + " " + EventToHTML._buildAnchor(obj) + " for " + EventToHTML._jobAnchor(obj.job);
    } else {
        console.error("Unknown event type " + obj.type);
        return "Unknown event";
    }
}

EventToHTML.render = function(e)
{
    var eventDate = new Date(e.time * 1000);
    var time = eventDate.toLocaleString();
    return time + " " + EventToHTML._renderObject(e.obj);
}
