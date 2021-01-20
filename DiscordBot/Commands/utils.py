from datetime import datetime
import discord

def formatString(oldStr):
    """
    Format string into separate lines

    Parameters
    ----------
    oldStr: string
        Old string to be Formatted

    Returns
    ----------
    numLines: int
        Number of lines the new string will take up
    newStr: string
        New string with new lines
    """

    LINE_LENGTH = 32
    strList = oldStr.split(" ")

    numLines = 1
    newStr = ""
    curLen = 0

    for word in strList:
        if (len(word) + curLen) > LINE_LENGTH:
            numLines += 1
            curLen = len(word) + 1
            newStr += ("\n" + word + " ")
        else:
            curLen += (len(word) + 1)
            newStr += (word + " ")

    return numLines, newStr


def getUsageEmbed(usageString):
    """
    Show the usage for addReward

    Parameters
    ----------
    guild : discord.Guild
        The server that we want to get information from

    Returns
    ----------
    discord.Embed
        Embedded message with the usage for addReward
    """

    now = datetime.today()
    embed = discord.Embed(title="Oops!", description="", timestamp=now)

    embed.set_footer(text="Kirbec Bot", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    embed.add_field(name="Usage", value=usageString)

    return embed

def getMissingPermissionsEmbed(errorString):
    """
    Show a message saying that the user does not have the correct permissions

    Returns
    ----------
    discord.Embed
        Embedded message saying the user doesn't have the correct permissions
    """

    now = datetime.today()
    embed = discord.Embed(title="Sorry!", description="", timestamp=now)

    embed.set_footer(text="Kirbec Bot", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    embed.add_field(name="Missing Permissions", value=errorString)

    return embed
