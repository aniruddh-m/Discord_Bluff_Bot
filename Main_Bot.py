import discord
from discord.ext import commands
import asyncio
from Bluff_Components import Player, Cards
import time

# Global Variables
command_prefix = '.'
client = commands.Bot(command_prefix = command_prefix)
client.remove_command('help')
TOKEN = ""
TimeGivenForPlayersToJoin = 10
TimeGivenForPlayerToMove = 30
TimeToChooseCardType = 10
TimeForBluffCall = 5
NumberOfConsecutiveTurnsUserAllowedToSkip = 3
WinnersList = []
GameStarted = False
CanAllowPlayersToJoin = False
NumberOfPlayersThatWantToStop = 0
AllPlayers = {}
PlayingDeck = None
MoveIsValid = False
ActiveGamePile = []
NewRoundStarted = False
CardTypeForRound = ''
AllowBluffCall = False
NumberOfPlayersPassedTurn = 0
CurrentPlayer = None
BluffCalled = False
GameServer = None

@client.event
async def on_ready():
    print("The bot is ready")

@client.command()
async def start(context, *numberOfDecks):
    #try:
        # Global Variables being accessed in the function
        global GameStarted, AllPlayers, GameServer
        GameServer = context.guild
        if len(numberOfDecks) > 0 and numberOfDecks[0].isdigit() \
        and not int(numberOfDecks[0]) <= 0 and not GameStarted and context.guild:
            GameStarted = True
            await context.send("Starting a new game. The current game can be joined using '.join'")
            await GetNamesOfAllParticipants()
            if len(AllPlayers) > 1:
                await context.send("The game has started. The cards will be shuffled and DMed to all the players.")
                # Dealing the cards
                await AssignAndDMCardsToPlayers(int(numberOfDecks[0]))
                await context.send("The game will now commence.")
                await StartPlayingBluff(context)

            else:
                await context.send("Need at least 2 people to play the game. The current game will close.")
                ResetAllParameters()
        else:
            if GameStarted:
                await context.send("There is already a game in progress. Wait for it to end or stop it using '.stop'")
            elif not context.guild:
                await context.send("This command can only be used in a server")
            else:
                await context.send("A non zero number of decks has to be specified to start a game")
    #except Exception as e:
        #print("Exception in Main_Bot.start:: {}".format(e))

async def GetNamesOfAllParticipants():
    # Global Variables being accessed in the function
    global CanAllowPlayersToJoin, TimeGivenForPlayersToJoin

    print("Waiting for players to join")
    start = time.time()
    CanAllowPlayersToJoin = True
    await asyncio.sleep(TimeGivenForPlayersToJoin)
    CanAllowPlayersToJoin = False
    print("Done waiting for players to join")
    print(time.time() - start)
    print(AllPlayers)

@client.command()
async def join(context):
    # Global Variables being accessed in the function
    global CanAllowPlayersToJoin, AllPlayers, GameServer

    if CanAllowPlayersToJoin and context.guild ==  GameServer:
        JoiningPlayer = context.author
        if not JoiningPlayer == client.user and not JoiningPlayer in AllPlayers:
            await context.channel.send("{} has been successfully added as a player.".format(context.author.mention))
            AllPlayers[JoiningPlayer] = Player()
    elif not context.guild:
        await context.send("This command can only be used in a server")
    else:
        await context.send("A game can only be joined within {} seconds after it has started".format\
        (TimeGivenForPlayersToJoin))

@client.command()
async def stop(context):
    global AllPlayers, GameStarted, NumberOfPlayersThatWantToStop, CurrentPlayer, GameServer
    if GameStarted and context.author in AllPlayers and context.guild\
        and not AllPlayers[context.author].WantToStopGame and GameServer == context.guild:
        AllPlayers[context.author].WantToStopGame = True
        NumberOfPlayersThatWantToStop += 1
        if NumberOfPlayersThatWantToStop < len(AllPlayers)//2+1:
            await context.send("Votes received to stop the game {}/{}".format\
            (NumberOfPlayersThatWantToStop, len(AllPlayers)//2+1))
        else:
            ResetAllParameters()
            await context.send("**The current game was stopped.**")

    elif not context.guild:
        await context.send("This command can only be used in a server")

    else:
        if not GameStarted:
            await context.send("There is no game being played currently")

def ResetAllParameters():
    global GameStarted, CanAllowPlayersToJoin, NumberOfPlayersThatWantToStop,\
        AllPlayers, PlayingDeck, MoveIsValid, ActiveGamePile, NewRoundStarted, \
            CardTypeForRound, AllowBluffCall, CurrentPlayer, NumberOfPlayersPassedTurn, GameServer
    GameStarted = False
    CanAllowPlayersToJoin = False
    NumberOfPlayersThatWantToStop = 0
    AllPlayers = {}
    PlayingDeck = None
    MoveIsValid = False
    ActiveGamePile = []
    NewRoundStarted = False
    CardTypeForRound = ''
    AllowBluffCall = False
    CurrentPlayer = None
    NumberOfPlayersPassedTurn = 0
    BluffCalled = False
    GameServer = None

async def AssignAndDMCardsToPlayers(NumberOfDecks):
    global PlayingDeck, AllPlayers

    PlayingDeck = Cards(NumberOfDecks)
    PlayingDeck.DistributeAmongPlayers(AllPlayers)

    for PlayerToGetCards in AllPlayers:
        await DMNumberOfCardsOfEachType(PlayerToGetCards)

async def ResetRoundParams():
    global MoveIsValid, ActiveGamePile, NewRoundStarted, \
        CardTypeForRound, AllowBluffCall, NumberOfPlayersPassedTurn, BluffCalled
    MoveIsValid = False
    ActiveGamePile = []
    NewRoundStarted = False
    CardTypeForRound = ''
    AllowBluffCall = False
    NumberOfPlayersPassedTurn = 0
    BluffCalled = False
    for Player in AllPlayers:
        AllPlayers[Player].PassedCurrentRound = False
        AllPlayers[Player].IsPlayerTurn = False

@client.command()
async def cards(context, *args):
    global GameStarted, AllPlayers
    if GameStarted:
        if context.author not in AllPlayers:
            await context.channel.send("Cards haven't been distributed yet")
        elif len(args):
            if args[0] == "all":
                embed = AllPlayers[context.author].getAllCardsWithPlayer()
                await context.author.send(embed = embed)
            else:
                await context.channel.send("Unrecognised argument.\n**Usage: '.cards [all]'**")
        else:
            await DMNumberOfCardsOfEachType(context.author)
    else:
        await context.channel.send("This command can only be used during the game.")

async def DMNumberOfCardsOfEachType(author):
    global AllPlayers
    if author in AllPlayers:
        embed = AllPlayers[author].getOrganizedCardsDistribution()
        await author.send(embed = embed)
    else:
        print("Main_Bot.DMNumberOfCardsOfEachType::\n", author, "NOT PRESENT")

async def StartPlayingBluff(ServerName):
    global AllPlayers, NewRoundStarted, CardTypeForRound, \
        CurrentPlayer, NumberOfPlayersPassedTurn, BluffCalled, NumberOfConsecutiveTurnsUserAllowedToSkip
    ListOfPlayers = list(AllPlayers.keys())
    await SendEmbedOfAllPlayers(ListOfPlayers, ServerName)
    PlayerIterator = 0
    while GameStarted:
        #for PlayerToPlay in ListOfPlayers:
        while PlayerIterator < len(ListOfPlayers):
            PlayerToPlay = ListOfPlayers[PlayerIterator]
            CurrentPlayer = PlayerToPlay
            await DMNumberOfCardsOfEachType(CurrentPlayer)
            if not NewRoundStarted:
                await StartNewRound(PlayerToPlay, ServerName)
                if CardTypeForRound:
                    NewRoundStarted = True
                    await ServerName.send("Card Type for this round is '{}'".format(CardTypeForRound))
                    await PlayerTurn(PlayerToPlay, ServerName)
            else:
                await PlayerTurn(PlayerToPlay, ServerName)
            # User has failed to enter valid moves more times than the allowable value
            if AllPlayers[PlayerToPlay].NumberOfConsecutiveTurnsMissed \
                >= NumberOfConsecutiveTurnsUserAllowedToSkip:
                await ServerName.send("{} has failed to enter valid moves in {} consecutive rounds.\nThey will be removed from the current game".format(\
                    PlayerToPlay.mention, NumberOfConsecutiveTurnsUserAllowedToSkip))
                del AllPlayers[PlayerToPlay]
                PlayerIterator = PlayerIterator % len(ListOfPlayers)
            # If the user is out of playable cards, they win
            if PlayerToPlay in AllPlayers and AllPlayers[PlayerToPlay].hasNoCardsLeft():
                await ServerName.send("{} doesn't have any more cards left.\nGGWP!".format(PlayerToPlay.mention))
                del AllPlayers[PlayerToPlay]
                PlayerIterator = PlayerIterator % len(ListOfPlayers)
            # If all the players have passed, a new round begins
            elif NumberOfPlayersPassedTurn == len(ListOfPlayers):
                await ResetRoundParams()
                await ServerName.send("All the players have passed their turns.\nStarting a new round.")
            # If bluff is called 
            elif BluffCalled:
                await ResetRoundParams()
                PlayerIterator = ListOfPlayers.index(CurrentPlayer)
            else:
                PlayerIterator = (PlayerIterator + 1) % len(ListOfPlayers)
            if len(AllPlayers) == 1:
                await ServerName.send("Only one player is left, the game has ended.")
                ResetAllParameters()
                break

async def SendEmbedOfAllPlayers(ListOfPlayers, ServerName):
    embed = discord.Embed(title = "Players that have joined this game")
    for Player in range(len(ListOfPlayers)):
        embed.add_field(name = ListOfPlayers[Player], value = Player, inline = False)
    await ServerName.send(embed = embed)

async def PlayerTurn(PlayerToPlay, ServerName):
    global AllPlayers, CurrentPlayer, MoveIsValid
    if not AllPlayers[PlayerToPlay].PassedCurrentRound:
        CurrentPlayer = PlayerToPlay
        await GetPlayerMove(PlayerToPlay, ServerName)
        if not AllPlayers[CurrentPlayer].PassedCurrentRound and MoveIsValid:
            MoveIsValid = False
            await BluffCall(PlayerToPlay, ServerName)
            AllPlayers[CurrentPlayer].NumberOfConsecutiveTurnsMissed = 0
        elif AllPlayers[CurrentPlayer].PassedCurrentRound and MoveIsValid:
            MoveIsValid = False
            await ServerName.send("{} have passed their turn for the current round.".format(PlayerToPlay.mention))
        elif not MoveIsValid:
            AllPlayers[CurrentPlayer].NumberOfConsecutiveTurnsMissed += 1

# Functions for rounds
@client.command()
async def round(context, *args):
    global AllPlayers, CardTypeForRound, NewRoundStarted, CurrentPlayer, GameServer
    print(".round called")
    if GameStarted and context.author == CurrentPlayer and not NewRoundStarted\
        and GameServer == context.guild:
        print(".round call successful")
        if len(args) > 0:
            CardTypeChosen = args[0]
            if context.author in AllPlayers:
                IsValidCardType, CardType = AllPlayers[context.author].IsValidCardType(CardTypeChosen)
                if IsValidCardType:
                    CardTypeForRound = CardType
                else:
                    await context.author.send("Invalid card type. Check the usage of '.round'.")
        else:
            await context.author.send("Incorrect usage.\nUsage: '.round <card_type>'.")
    else:
        if not GameStarted:
            await context.author.send("This command can only be used in a game.")

async def StartNewRound(PlayerToPlay, ServerName):
    global TimeToChooseCardType
    await ServerName.send("{} choose what type of card has to be played in this round using '.round'.".\
        format(PlayerToPlay.mention))
    CountTimesSlept = 0
    while CountTimesSlept < int(TimeToChooseCardType) and not CardTypeForRound:
        await asyncio.sleep(1)
        CountTimesSlept += 1

# Functions for players' moves
@client.command()
async def move(context):
    global AllPlayers
    if GameStarted and context.author in AllPlayers and AllPlayers[context.author].IsPlayerTurn \
        and not AllPlayers[context.author].PassedCurrentRound:
        await checkIfValidMove(context)
    elif not GameStarted or not context.author in AllPlayers:
        await context.send("This command can only be used once a game has commenced.")
    elif not AllPlayers[context.author].IsPlayerTurn:
        await context.send("It is not your turn yet. Wait patiently for your turn.")
    elif AllPlayers[context.author].PassedCurrentRound:
        await conext.send("{}, you have already passed you turn in this round.".\
            format(context.author.mention))        

@client.command()
async def done(context):
    global AllPlayers, NumberOfPlayersPassedTurn, MoveIsValid
    if GameStarted and context.author in AllPlayers and AllPlayers[context.author].IsPlayerTurn\
         and not AllPlayers[context.author].PassedCurrentRound:
        AllPlayers[context.author].PassedCurrentRound = True
        MoveIsValid = True
        NumberOfPlayersPassedTurn = NumberOfPlayersPassedTurn + 1
    elif not GameStarted or not context.author in AllPlayers:
        await context.send("This command can only be used once a game has commenced.")
    elif not AllPlayers[context.author].IsPlayerTurn:
        await context.send("It is not your turn yet. Wait patiently for your turn.")
    elif AllPlayers[context.author].PassedCurrentRound:
        await conext.send("{}, you have already passed you turn in this round.".\
            format(context.author.mention))

async def GetPlayerMove(PlayerToPlay, ServerName):
    global AllPlayers, MoveIsValid, ActiveGamePile, CurrentMove
    await ServerName.send("*{} send your move on DM*".format(PlayerToPlay.mention))
    await AcceptPlayerMove(AllPlayers[PlayerToPlay])
    if MoveIsValid and not AllPlayers[PlayerToPlay].PassedCurrentRound:
        ActiveGamePile.append(CurrentMove)
        print(ActiveGamePile)
        await ServerName.send("{} has played {} card(s).".format(PlayerToPlay.mention, len(ActiveGamePile[-1])))
    else:
        print("Current player's move is invalid") 

async def AcceptPlayerMove(PlayerToPlay):
    global TimeGivenForPlayerToMove, MoveIsValid
    PlayerToPlay.IsPlayerTurn = True
    CountTimesSlept = 0
    while CountTimesSlept < int(TimeGivenForPlayerToMove) and not MoveIsValid:
        await asyncio.sleep(1)
        CountTimesSlept += 1
    PlayerToPlay.IsPlayerTurn = False

async def checkIfValidMove(context):
    global AllPlayers, MoveIsValid, CurrentMove
    MoveIsValid, CurrentMove = AllPlayers[context.author].ValidateAndUpdateMove(context.message.content)
    if not MoveIsValid:
        await context.author.send("The move is invalid, please enter a valid move.")

# Functions for calling bluff
async def BluffCall(PlayerToPlay, ServerName):
    global AllowBluffCall, TimeForBluffCall, CardTypeForRound
    if CardTypeForRound:
        await ServerName.send("{}'s bluff can be called now".format(PlayerToPlay.mention))
        AllowBluffCall = True
        CountTimesSlept = 0
        while CountTimesSlept < int(TimeForBluffCall) and AllowBluffCall:
            await asyncio.sleep(1)
            CountTimesSlept += 1
        await ServerName.send("Time to call bluff is over.")
        AllowBluffCall = False

@client.command()
async def call(context):
    global CurrentPlayer, ActiveGamePile, CardTypeForRound, AllPlayers, AllowBluffCall, BluffCalled
    if GameStarted and context.guild and AllowBluffCall and\
        not context.author == CurrentPlayer and CardTypeForRound and context.author in AllPlayers:
        AllowBluffCall = False
        BluffCalled = True
        LastMovePlayed = ActiveGamePile[-1]
        PlayerBluffed = await CheckIfBluff(LastMovePlayed)
        if PlayerBluffed:
            await context.send("{} had bluffed, and will now pick up all the cards.\nWell played {}".\
                format(CurrentPlayer.mention, context.author.mention))
            AllPlayers[CurrentPlayer].pickUpCards(ActiveGamePile)
            CurrentPlayer = context.author
        else:
            await context.send("{} had not bluffed.\n{} will now pick up all the cards.".\
                format(CurrentPlayer.mention, context.author.mention))
            AllPlayers[context.author].pickUpCards(ActiveGamePile)
    else:
        if not GameStarted:
            await context.send("This command can only be used in a game.")
        elif not context.guild:
            await context.send("This command can only be used in servers.")
        elif context.author == CurrentPlayer:
            await context.send("You can not call your own plays lol.")
        elif not CardTypeForRound:
            await context.send("The round hasn't started yet. You can only use this\
                 after a player has played his move")
        elif not AllowBluffCall:
            await context.send("Can only use this within the time allotted after a player plays his move")

async def CheckIfBluff(LastMovePlayed):
    global CardTypeForRound
    print(CardTypeForRound)
    for CardPlayed in LastMovePlayed:
        print(CardPlayed)
        if CardTypeForRound not in CardPlayed and "Joker" not in CardPlayed:
            return True
    return False

@client.command()
async def help(context):
    embed = discord.Embed(title = "HELP")
    embed.add_field(name=".start <Number_Of_Decks>", value="Used to start a game with the number decks specified. Eg: .start 1", inline=False)
    embed.add_field(name=".join", value="Used to join a game that has been started before.", inline=False)
    embed.add_field(name=".round <Card_Type>", value="Used to specify what type of card has to be played in the current round. Eg: .round a, round 2, .round j", inline=False)
    embed.add_field(name=".move <Card_Type1>-<Number_Of_Cards_Of_Specified_Type>, <Card_Type2>-<Number_Of_Cards_Of_Specified_Type>, ...", value="Used to play your move. If multiple types have to be specified, separate them with commas. The last set specified shouldn't be followed by a comma. Eg1: .move a-1. Eg2: .move a-1, 2-2, 3-2, jkr-1", inline=False)
    embed.add_field(name=".done", value="Used when you want to pass your turns in the current round. This can only be used if it is your move.", inline=False)
    embed.add_field(name=".call", value="Used to call someone's bluff. This can only be used after someone has played their move.", inline=False)
    embed.add_field(name=".stop", value="Used when you want to end the current game.", inline=False)
    embed.add_field(name=".cards [all]", value="Used when you want view you the number of cards of each type that the player has. If the optional 'all' argument is present, the cards that the player has are displayed.", inline=False)
    embed.set_footer(text="Use 'a' for Ace(s), 'j' for Jack(s), 'q' for Queen(s), 'k' for Kings and 'jkr' for Joker(s)")
    await context.send(embed = embed)

if __name__ == "__main__": 
    client.run(TOKEN)