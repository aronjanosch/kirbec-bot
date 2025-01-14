import firebase_admin
from datetime import datetime
from firebase_admin import credentials, firestore
from collections import OrderedDict
import json
from datetime import datetime
from pytz import timezone
import datetime as dt
from firebase_config import firebase_config_dict

class Fire:
    """
    Creates an instance of the Google Firebase

    Attributes
    __________
    __db (private firebase.client obj): database for POST and GET requests

    Functions
    __________
    incrementTimes(guild, members)
        Increment time accumulation for *total* and *day* in __db
    fetchAllMembers(guild) -> dict: { discord.member.id: discord.member.display_name }
        Fetch all members in the guild
    fetchTotalTimes(guild) -> dict: { discord.member.id: int }
        Fetch total time for members in the guild
    fetchAllDateTimes(guild) -> dict: { date: { discord.member.id: int } }
        Fetch all members' times organized by date
    fetchDiscordPoints(guild) -> dict: { discord.member.id: int }
        Fetch all members' discord points for the server
    postNewDiscordPoints(guild, user, newPoints)
        Updates the discord points for a user
    postNewReward(guild, rewardTitle, rewardCost)
        Pushes a new reward to the database
    fetchAllRewards(guild) -> dict: { rewardTitle(str) : cost(int) }
        Shows all Discord Points rewards for the guild
    fetchAllBets(guild) -> dict: { betId(int): betDict(dict) }
        Shows all proposed bets for the guild
    postNewBet(guild, userId, betTitle, betOptions, betStartedAt) -> betId(int)
        Creates a new bet in the database
    postCloseBet(guild, user, betId) -> betDict(str), errorString(str)
        Marks a bet as closed in the database
    async def postCompleteBet(guild, user, betId, winningOptionId) ->  betDict(dict), userRewards(dict), errorString(str)
        Marks a bet as completed in the database and pays out the winners
    postBet(guild, user, betId, betOption, betAmount) -> betDict(dict), errorString(str)
        Adds an amount for the user for a bet option to the database
    postFeedback(guild, userId, feedbackString)
        Posts feedback to the database for the guild/userId

    """

    __db = None

    def __init__(self):
        # Checks to see if Firebase was already initialized in the applicaiton
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config_dict)
            firebase_admin.initialize_app(cred)
        self.__db = firestore.client()

    async def fetchAllMembers(self, guild):
        """
        Fetch all members in the guild

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to get all the members from

        Returns
        ----------
        dict: { discord.member.id: discord.member.display_name }
        """

        member_dict = {}
        async for member in guild.fetch_members():
            member_dict[member.id] = member.display_name

        return member_dict

    def fetchTotalTimes(self, guild):
        """
        Fetch total times for members in the guild

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to get information from

        Returns
        ----------
        dict: { discord.member.id: int }
        """

        try:
            doc_ref = self.__db.collection(str(guild.id)).document('total')
            d = doc_ref.get().to_dict()

            if d == None:
                return {}

            d = d['users']

            return d
        except:
            print('Error in fetchTotalTimes')
            return {}


    def incrementTimes(self, guild, members):
        """
        Increment time accumulation for *total* and *day* in __db

        Parameters
        ----------
        guild : discord.Guild
            The server that the members belong to
        members : list(discord.Member)
            Update times for these users
        """

        if members == None or members == []:
            return

        self.__updateTotalTimes(guild, members)
        self.__updateDayTimes(guild, members)
        if len(members) >= 1:
            self.__increaseDiscordPoints(guild, members)


    def fetchAllDateTimes(self, guild):
        """
        Fetch all members' times organized by date

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to get information from

        Returns
        ----------
        dict: { date: { discord.member.id: int } }
        """

        try:
            doc_ref = self.__db.collection(str(guild.id)).document('date')
            d = doc_ref.get().to_dict()

            if d == None:
                return {}

            # Sort the data by most recent date
            ordered_data = OrderedDict(sorted(d.items(), key = lambda x:datetime.strptime(x[0], '%m/%d/%Y'), reverse=True))
            return ordered_data
        except:
            print("FetchAllDateTimes Error")
            return {}

# --------------------- Discord Points --------------------------
    def fetchDiscordPoints(self, guild):
        """
        Fetch all members' discord points in the server

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to get information from

        Returns
        ----------
        dict: { discord.member.id: int }
        """

        try:
            doc_ref = self.__db.collection(str(guild.id)).document('discordPoints')
            d = doc_ref.get().to_dict()

            if d == None:
                return {}

            return d
        except:
            print('Error in fetchDiscordPoints')
            return {}

    def postNewDiscordPoints(self, guild, userid, newPoints):
        """
        Updates the discord points for a user

        Parameters
        ----------
        guild     : discord.Guild
            The server that we want to push information to
        user      : discord.Member if in guild, discord.User otherwise
            The user whose points should be updated
        newPoints : int
            The updated amount of points the user should have
        """
        try:
            doc_ref = self.__db.collection(str(guild.id)).document('discordPoints')
            d = doc_ref.get().to_dict()

            if d == None:
                return {}

            d[userid] = newPoints

            doc_ref.set(d)
        except Exception as e:
            print(e)
            print('Error in postNewDiscordPoints')
            return {}

    def postNewReward(self, guild, rewardTitle, rewardCost):
        """
        Pushes a new reward to the database

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to get info from
        rewardTitle : string
            A string representing the new award
        rewardCost : int
            The cost of the reward
        """
        doc_ref = self.__db.collection(str(guild.id)).document('rewards')

        rewards_dict = self.fetchAllRewards(guild)
        rewards_dict[rewardTitle] = rewardCost

        doc_ref.set(rewards_dict)


    def fetchAllRewards(self, guild):
        """
        Shows all Discord Points rewards for the guild

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to get info from
        """
        try:
            doc_ref = self.__db.collection(str(guild.id)).document('rewards')
            d = doc_ref.get().to_dict()

            if d == None:
                return {}

            return d
        except:
            return {}

# ---------------------- Discord Bets ---------------------------
    def fetchAllBets(self, guild):
        """
        Fetch all bets within the discord

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to get information from

        Returns
        ----------
        d: { betId(int): betDict(dict) }
        """

        try:
            doc_ref = self.__db.collection(str(guild.id)).document('bets')
            d = doc_ref.get().to_dict()

            if d == None:
                return {}

            return d
        except:
            return {}

    def postNewBet(self, guild, userId, betTitle, betOptions, betStartedAt):
        """
        Create a new bet in the database

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to push information to
        userId: int
            The id of the user posting the bet
        betTitle: string
            The title of the bet
        betOptions: { betOption(string) : amountBet(int) }
            All of the options for the bet and the total amount wagered on them
        betStartedAt: string
            A string representing when the bet was started

        Returns
        ----------
        betId: int
            An int representing the id of the bet we just created
        """
        try:
            doc_ref = self.__db.collection(str(guild.id)).document('bets')

            d = self.fetchAllBets(guild)

            if 'numBets' in d:
                d['numBets'] = int(d['numBets']) + 1
            else: 
                d['numBets'] = 1

            d[str(d['numBets'])] = {
                "acceptedBy": {},
                "options": betOptions,
                "betTitle": betTitle,
                "startedAt": betStartedAt,
                "startedBy": userId,
                "completed": False,
                "winningOption": "",
                "closed": False,
                "betId" : d['numBets'],
            }

            doc_ref.set(d)

            # We return the value of the betId that we just created (based off of numBets)
            return d['numBets']
        except Exception as e:
            print(e)
            print("Error posting new bet to Firebase")
            
            return -1

    def postCloseBet(self, guild, userId, betId):
        """
        Marks a bet as 'closed' within the database

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to push information to
        user: discord.Member
            The user closing the bet
        betId: str
            The id of the bet we are attempting to close

        Returns
        ----------
        betDict: dict
            The bet we attempted to close
        errorString: str
            The string representing the error if one occurred
        """

        try:
            bet_doc_ref = self.__db.collection(str(guild.id)).document('bets')
            betDict = bet_doc_ref.get().to_dict()

            if not betId in betDict:
                return None, "Not a valid Bet Id"
            if betDict[betId]['startedBy'] != userId and not userId.guild_permissions.administrator:
                return None, "Only the person that started the bet or an admin can close submissions for the bet"

            betDict[betId]["closed"] = True
            bet_doc_ref.set(betDict)

            return betDict[betId], None
        except Exception as e:
            print(e)
            print("Error closing bet")

            return None, "Error closing bet in the database"

    async def postCompleteBet(self, guild, user, betId, winningOptionId):
        """
        Marks a bet as 'completed' within the database

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to push information to
        user: discord.Member
            The user completing the bet
        betId: str
            The id of the bet we are attempting to complete
        winningOptionId: str
            The id of the option that won the bet

        Returns
        ----------
        betDict: dict
            The bet we attempted to complete
        userRewards: dict {userId : amountWon}
            The dictionary with ids representing how many points each user won 
        errorString: str
            The string representing the error if one occurred
        """
        
        try:
            bet_doc_ref = self.__db.collection(str(guild.id)).document('bets')
            points_doc_ref = self.__db.collection(str(guild.id)).document('discordPoints')

            betDict = bet_doc_ref.get().to_dict()
            pointsDict = points_doc_ref.get().to_dict()
            memberDict = await self.fetchAllMembers(guild)

            userId = str(user.id)

            if not betId in betDict:
                return None, None, "Not a valid Bet Id"
            elif betDict[betId]['startedBy'] != user.id and not user.guild_permissions.administrator:
                return None, None, "Only the person that started the bet or an admin can complete/payout the bet"
            elif betDict[betId]["completed"]:
                return None, None, "Bet has already been completed"
            elif int(winningOptionId) > len(betDict[betId]["options"]) or int(winningOptionId) <= 0:
                return None, None, "Not a valid Bet Option"

            optionList = sorted(list(betDict[betId]["options"].keys()))
            betDict[betId]["completed"] = True
            betDict[betId]["winningOption"] = optionList[int(winningOptionId)-1]

            # Calculate the total amount of points in the pool
            totalPointAmount = 0
            for key in betDict[betId]["options"]:
                totalPointAmount += int(betDict[betId]["options"][key])

            # Calculate the multipliers for each option
            totalPointMultipliers = {}
            for key in betDict[betId]["options"]:
                if int(betDict[betId]["options"][key]) != 0:
                    totalPointMultipliers[key] = totalPointAmount / int(betDict[betId]["options"][key])
            
            # Calculate the rewards for each user
            userRewards = {}
            for key in betDict[betId]["acceptedBy"]:
                userBet = betDict[betId]["acceptedBy"][key]
                if userBet["betOption"] == betDict[betId]["winningOption"]:
                    pointAmount = int(int(userBet["amount"]) * totalPointMultipliers[userBet["betOption"]])
                    userRewards[memberDict[int(key)]] = pointAmount
                    print(pointsDict)
                    pointsDict[str(key)] = int(pointsDict[str(key)]) + pointAmount

            bet_doc_ref.set(betDict)
            points_doc_ref.set(pointsDict)

            return betDict[betId], userRewards, None
        except Exception as e:
            print(e)
            print("Error completing bet")

            return None, None, "Error completing bet in the database"

    def postBet(self, guild, user, betId, betOption, betAmount):
        """
        Adds a bet for a user to an open bet

        Parameters
        ----------
        guild : discord.Guild
            The server that we want to push information for
        user: discord.Member
            The user adding a bet
        betId: str
            The id of the bet we are attempting to add an individual bet to
        betOption: str
            The id of the bet option the user wants to bet for
        betAmount: int
            The amount the user wants to bet for that option

        Returns
        ----------
        betDict: dict
            The bet the user bet on with updated information
        errorString: str
            The string representing the error if one occurred
        """
        try:
            bet_doc_ref = self.__db.collection(str(guild.id)).document('bets')
            points_doc_ref = self.__db.collection(str(guild.id)).document('discordPoints')

            betDict = self.fetchAllBets(guild)
            pointsDict = self.fetchDiscordPoints(guild)
            userId = str(user.id)

            if not userId in pointsDict or int(pointsDict[userId]) < betAmount:
                return None, "Not discord points"
            elif not betId in betDict:
                return None, "Not a valid Bet Id"
            elif betDict[betId]["closed"] or betDict[betId]["completed"]:
                return None, "Bet no longer has open submissions"
            elif int(betOption) > len(betDict[betId]["options"]) or int(betOption) <= 0:
                return None, "Not a valid Bet Option"
            elif userId in betDict[betId]["acceptedBy"]:
                optionList = sorted(list(betDict[betId]["options"].keys()))
    
                if betDict[betId]["acceptedBy"][userId]["betOption"] != optionList[int(betOption)-1]:
                    return None, "Cannot bet for more than one option"

            # Bet options are sorted for Ids
            optionList = sorted(list(betDict[betId]["options"].keys()))
            betDict[betId]["options"][optionList[int(betOption)-1]] += betAmount
            betDict[betId]["acceptedBy"][userId] = {"betOption": optionList[int(betOption)-1], "amount": betAmount}
            pointsDict[userId] = int(pointsDict[userId]) - betAmount

            bet_doc_ref.set(betDict)
            points_doc_ref.set(pointsDict)

            return betDict[betId], None
            
        except Exception as e:
            print(e)
            print("Error posting bet to Firebase")

            return None, "Error sending information to the database"

    # -------------  Misc. Functions -----------------------
    def postFeedback(self, guild, userId, feedbackString):
        """
        Post feedback to the database

        Parameters
        ----------
        guild : discord.Guild
            The guild the feedback is for
        userId : int
            The if of the user that left the feedback
        feedbackString: string
            A string representing the feedback 
        """
        self.__db.collection('feedback').add({
            'feedback': feedbackString, 
            'user': userId,
            'guild': guild,
        })


# ---------- MARK: - Private Methods ----------
    def __updateTotalTimes(self, guild, members):
        """
        Increment time accumulation for *total* in __db

        Parameters
        ----------
        guild : discord.Guild
            The server that the members belong to
        members : list(discord.Member)
            Update times for these users
        """
        doc_ref = self.__db.collection(str(guild.id)).document('total')

        d = self.fetchTotalTimes(guild)

        if d == None:
            return {}

        for member in members:
            if str(member.id) in d:
                d[str(member.id)] += 1
            else:
                d[str(member.id)] = 1

        doc_ref.set({
            'users': d
        })

    def __updateDayTimes(self, guild, members):
        """
        Increment time accumulation for *today* in __db

        Parameters
        ----------
        guild : discord.Guild
            The server that the members belong to
        members : list(discord.Member)
            Update times for these users
        """

        td = dt.timedelta(hours=6)
        shiftedNow = datetime.today() - td
        curDateStr = shiftedNow.strftime('%m/%d/%Y')

        doc_ref = self.__db.collection(str(guild.id)).document('date')

        allDateTimes = self.fetchAllDateTimes(guild)
        d = {}

        if allDateTimes == {} or allDateTimes == None or not curDateStr in allDateTimes.keys():
            d = {}
        else:
            d = allDateTimes[curDateStr]

        for member in members:
            if str(member.id) in d:
                d[str(member.id)] += 1
            else:
                d[str(member.id)] = 1

        allDateTimes[curDateStr] = d

        doc_ref.set(allDateTimes)

    def __increaseDiscordPoints(self, guild, members):
        """
        Increase discord points for each user in the discord

        Parameters
        ----------
        guild : discord.Guild
            The server that the members belong to
        members : list(discord.Member)
            Update times for these users
        """
        doc_ref = self.__db.collection(str(guild.id)).document('discordPoints')

        d = self.fetchDiscordPoints(guild)

        if d == None:
            d = {}

        for member in members:
            if str(member.id) in d:
                d[str(member.id)] += 0
            else:
                d[str(member.id)] = 100

        doc_ref.set(d)
