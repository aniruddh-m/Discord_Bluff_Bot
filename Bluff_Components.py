import random
import re
import discord

class Player:
    def __init__(self):
        self.AllCardsDict = {}
        self.cardValues = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Joker"]
        self.IsPlayerTurn = False
        self.PassedCurrentRound = False
        self.MappingFromMovesToCardValues = \
        {
            'a': "Ace",
            'ace': "Ace",
            '2': '2',
            '3': '3',
            '4': '4',
            '5': '5',
            '6': '6',
            '7': '7',
            '8': '8',
            '9': '9',
            '10': '10',
            'j': "Jack",
            'jack': "Jack",
            'q': "Queen",
            'queen': "Queen",
            'k': "King",
            'king': "King",
            'jkr': "Joker",
            'joker': "Joker"
        }
        self.NumberOfConsecutiveTurnsMissed = 0
        self.WantToStopGame = False

    def AssignInitialCards(self, CardsToAssign):
        AllCardsArray = CardsToAssign
        self.UpdateDictionaryOfCards(AllCardsArray)
    
    def UpdateDictionaryOfCards(self, AllCardsArray):
        cardValuesSearchRegex = '(' + '|'.join(self.cardValues) + ')'
        for Card in AllCardsArray:
            currentCardValueSearch = re.search(cardValuesSearchRegex, Card, re.IGNORECASE)
            if currentCardValueSearch:
                currentCardValue = currentCardValueSearch.group(1)
                if currentCardValue not in self.AllCardsDict:
                    self.AllCardsDict[currentCardValue] = []
                self.AllCardsDict[currentCardValue].append(Card)

    def getAllCardsWithPlayer(self):
        embed=discord.Embed(title="All the cards that you have:")
        for cardValue in self.cardValues:
            if cardValue in self.AllCardsDict:
                embed.add_field(name=cardValue + 's', value=self.AllCardsDict[cardValue], inline=False)
            else:
                embed.add_field(name=cardValue + 's', value="No cards present", inline=False)
        return embed

    def getOrganizedCardsDistribution(self):
        embed=discord.Embed(title="Number of cards of each type:")
        for cardValue in self.cardValues:
            if cardValue in self.AllCardsDict:
                embed.add_field(name=cardValue+'s', value=len(self.AllCardsDict[cardValue]), inline=False)
            else:
                embed.add_field(name=cardValue+'s', value='0', inline=False)
        return embed

    def ValidateAndUpdateMove(self, PlayerMove):
        try:
            ActualPlayerMove = PlayerMove.replace(".move", "").lower()
            Card_Value_Pairs = ActualPlayerMove.replace(' ', '').split(',')
            CardsPlayed = []
            print(Card_Value_Pairs)
            # Check if move is valid
            for Card_Value in Card_Value_Pairs:
                CardValue, CardNumber = Card_Value.split('-')
                if not CardNumber.isdigit():
                    return False, []
                CardNumber = int(CardNumber)

                if CardValue in self.MappingFromMovesToCardValues and \
                len(self.AllCardsDict[self.MappingFromMovesToCardValues[CardValue]]) >= CardNumber:
                    continue
                else:
                    return False, []
            # If move is valid, update it
            for Card_Value in Card_Value_Pairs:
                CardValue, CardNumber = Card_Value.split('-')
                if not CardNumber.isdigit():
                    return False, []
                CardNumber = int(CardNumber)

                if CardValue in self.MappingFromMovesToCardValues and \
                len(self.AllCardsDict[self.MappingFromMovesToCardValues[CardValue]]) >= CardNumber:
                    CardsPlayed = CardsPlayed + self.AllCardsDict[self.MappingFromMovesToCardValues[CardValue]][:CardNumber]
                    self.AllCardsDict[self.MappingFromMovesToCardValues[CardValue]] = \
                        self.AllCardsDict[self.MappingFromMovesToCardValues[CardValue]][CardNumber:]
                else:
                    return False, []
            return True, CardsPlayed
            
        except Exception as e:
            print("Error in Bluff_Components.ValidateAndUpdateMove:: {}".format(e))
            return False, []

    def IsValidCardType(self, CardTypeChosen):
        CardTypeChosen = CardTypeChosen.lower()
        if CardTypeChosen in self.MappingFromMovesToCardValues \
            and not CardTypeChosen == "jkr" and not CardTypeChosen == "joker":
            return True, self.MappingFromMovesToCardValues[CardTypeChosen]
        else:
            return False, ""

    def pickUpCards(self, ActiveGamePile):
        for MoveByPlayer in ActiveGamePile:
            self.UpdateDictionaryOfCards(MoveByPlayer)

    def hasNoCardsLeft(self):
        for CardType in self.AllCardsDict:
            if not self.AllCardsDict[CardType] == []:
                return False
        return True

class Cards:
    def __init__(self, NumberOfDecks):
        suits = ["Clubs", "Diamonds", "Hearts", "Spades"]
        cardValues = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
        numberOfJokers = 2

        SingleDeck = []
        for suit in suits:
            for card in cardValues:
                SingleDeck.append("{} of {}".format(card, suit))
        SingleDeck = SingleDeck + ["Joker"]*numberOfJokers
        self.AllCards = SingleDeck*NumberOfDecks
        random.shuffle(self.AllCards)
        self.TotalNumberOfCards = len(self.AllCards)
        print("Total Number of Cards", self.TotalNumberOfCards)
    
    def DistributeAmongPlayers(self, AllPlayers):
        # Create piles of cards to disctribute to the players
        TotalNumberOfPlayers = len(AllPlayers)
        AverageNumberOfCardsPerPerson = self.TotalNumberOfCards // (TotalNumberOfPlayers)
        NumberOfCardsRemaining = self.TotalNumberOfCards % (TotalNumberOfPlayers)
        print("Total number of players: {}\nAverage cards {}\nLeftOver {}".format(TotalNumberOfPlayers, AverageNumberOfCardsPerPerson, NumberOfCardsRemaining))
        DistributionOfCards = [self.AllCards[i*AverageNumberOfCardsPerPerson: (i+1)*AverageNumberOfCardsPerPerson]\
        for i in range(len(AllPlayers))]

        if NumberOfCardsRemaining:
            PlayerToGiveExtraCard = 0
            for ExtraCard in self.AllCards[-NumberOfCardsRemaining:]:
                DistributionOfCards[PlayerToGiveExtraCard % TotalNumberOfPlayers].append(ExtraCard)
                PlayerToGiveExtraCard += 1
        
        # Distribute the cards among players
        i = 0
        for PlayerToGetCards in AllPlayers:
            AllPlayers[PlayerToGetCards].AssignInitialCards(DistributionOfCards[i])
            i += 1