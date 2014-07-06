def describeTime(seconds):
    days = seconds / 60 / 60 / 24
    hours = seconds / 60 / 60
    if hours < 1:
        return "less than an hour"
    elif days < 1:
        return "%d hours" % hours
    else:
        return "%d days" % days
