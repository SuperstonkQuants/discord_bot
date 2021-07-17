class Tokens(object):
    DISCORD_TOKEN = "token here"


class MessageIDs(object):
    RULES_MSGID = 854535314436521984


class ChannelIDs(object):
    XANASTROLOGY = 853107900029075486
    VEGAS = 861767811604676628


class FilePaths(object):
    ROOT_PATH = ""
    COGS_PATH = ""
    STORAGE_PATH = ""
    IMAGES_PATH = ""


class Timezones(object):
    """ identifiers are often shorter and easier to use for members. hence abbrevations are stores seperately
    
    """

    identifier = {
        "EST": (
            "Eastern Standard Time",
            "EST"
        ),
        "PST": (
            "Pacific Standard Time",
            "PST8PDT"
        ),
        "CST":	(
            "Central Standard Time",
            "CST6CDT"
        ),
        "CET": (
            "Central European Time",
            "CET"
        ),
        "CAT": (
            "Central Africa Time",
            "Africa/Maputo"
        ),
        "AEST": (
            "Australian Eastern Standard Time",
            "EST"
        ),
        "AWST": (
            "Australian Western Standard Time",
            "Australia/West"
        ),
        "AKST": (
            "Alaska Standard Time",
            "US/Alaska"
        ),
        "HKT": (
            "Hong Kong Time",
            "Asia/Hong_Kong"
        ),
        "KST": (
            "Korea Standard Time",
            "Asia/Seoul"
        ),
        "GMT": (
            "Greenwich Mean Time",
            "GMT"
        ),
        "EDT": (
            "Eastern Daylight Time",
            "Canada/Eastern"
        )
    }
