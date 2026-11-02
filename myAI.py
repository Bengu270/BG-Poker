from poker.action import Action
from poker.game_state import GameState


def myAI(state: GameState) -> Action:
    hand = state.my_player.hole_cards
    communityCards = state.community_cards
    handCardRanks = []
    communityCardRanks = []
    handCardSuits = []
    communityCardSuits = []
    for item in hand:
        match item.rank.value:
            case 'one':
                handCardRanks.append(1)
            case 'two':
                handCardRanks.append(2)
            case 'three':
                handCardRanks.append(3)
            case 'four':
                handCardRanks.append(4)
            case 'five':
                handCardRanks.append(5)     
            case 'six':
                handCardRanks.append(6)
            case 'seven':
                handCardRanks.append(7)
            case 'eight':
                handCardRanks.append(8)
            case 'nine':
                handCardRanks.append(9)
            case 'ten':
                handCardRanks.append(10)
            case 'jack':
                handCardRanks.append(11)
            case 'queen':
                handCardRanks.append(12)
            case 'king':
                handCardRanks.append(13)
            case 'ace':
                handCardRanks.append(14)

        handCardSuits.append(item.suit.value)
    for item in communityCards:
            match item.rank.value:
                case 'one':
                    communityCardRanks.append(1)
                case 'two':
                    communityCardRanks.append(2)
                case 'three':
                    communityCardRanks.append(3)
                case 'four':
                    communityCardRanks.append(4)
                case 'five':
                    communityCardRanks.append(5)     
                case 'six':
                    communityCardRanks.append(6)
                case 'seven':
                    communityCardRanks.append(7)
                case 'eight':
                    communityCardRanks.append(8)
                case 'nine':
                    communityCardRanks.append(9)
                case 'ten':
                    communityCardRanks.append(10)
                case 'jack':
                    communityCardRanks.append(11)
                case 'queen':
                    communityCardRanks.append(12)
                case 'king':
                    communityCardRanks.append(13)
                case 'ace':
                    communityCardRanks.append(14)

            communityCardSuits.append(item.suit.value)

    cardRanks = handCardRanks + communityCardRanks
    cardSuits = handCardSuits + communityCardSuits


    suits = ['club', 'diamond', 'heart', 'spade']

    to_call = max(player.chips_bet for player in state.players) - state.my_player.chips_bet

    numPairs = 0
    pairs = []
    numTriples = 0
    numQuads = 0
    numSameSuit = 0
    numInStraight = 0

    for i in range(1, 15):
        match cardRanks.count(i):
            case 2:
                numPairs += 1
                pairs.append(i)
            case 3:
                numTriples += 1
            case 4:
                numQuads += 1
    for i in [r for r in range(1, 15) if r not in handCardRanks]:
        match communityCardRanks.count(i):
            case 2:
                numPairs -= 1
                if i in pairs:
                    pairs.remove(i)
            case 3:
                numTriples -= 1
            case 4:
                numQuads -= 1

    longestSuit = ''
    for suit in suits:
        suitCount = cardSuits.count(suit)
        if suitCount > numSameSuit and (suit in handCardSuits):
            numSameSuit = suitCount
            longestSuit = suit

    highestSuitInHand = 0
    if cardSuits[0] == longestSuit:
        highestSuitInHand = cardRanks[0]
    if cardSuits[1] == longestSuit:
        if cardRanks[1] > highestSuitInHand:
            highestSuitInHand = cardRanks[1]

    cardRanks.sort()
    cardRanks = list(dict.fromkeys(cardRanks))
    longestStraight = 1
    for i in range(len(cardRanks)-1):
        if (cardRanks[i] + 1) == (cardRanks[i+1]):
            longestStraight += 1
        else:
            if (longestStraight > numInStraight):
                numInStraight = longestStraight
            longestStraight = 1
            
    numInStraight = max(numInStraight, longestStraight)
    if numPairs <0:
        numPairs = 0
    if numTriples <0:
        numTriples = 0
    if numQuads <0:
        numQuads = 0


    # print(cardRanks, cardSuits, numPairs, pairs, numTriples, numQuads, numInStraight, numSameSuit, longestSuit, highestSuitInHand)


    if (len(communityCards)) == 0:

        if (numPairs >= 1 or min(handCardRanks) >= 11) and (state.my_player.chips_bet <= 50):
            if max(pairs, default=0) >=10:
                return Action.raise_by(25)
            else:
                return Action.raise_by(10)
        elif to_call > 0 and to_call < 20 and (state.my_player.chips_bet <= 20):
            return Action.call() 
        elif to_call > 0:
            return Action.fold()
        else:
            return Action.check()
    
    elif (len(communityCards)) == 3:
        confidence = 10*numPairs + max(pairs, default=0) + 50*numTriples + 100*numQuads + (100 if numInStraight >= 5 else (12 if numInStraight == 4 else 0)) + (100 if numSameSuit >= 5 else (15 if numSameSuit == 4 and (cardSuits[0] == cardSuits[1] or highestSuitInHand >= 10) else 0))
        # print(confidence)

        if (confidence <10):
            return Action.check() if to_call == 0 else Action.fold()
        elif (confidence >= 50):
            if True: # (state.my_player.chips_bet <= 50):
                if(state.chips_in_pot // 2 <= 50):
                    return Action.raise_by(50)
                else:
                    return Action.raise_by(state.chips_in_pot // 2)
        elif (confidence >= 20):
            if state.my_player.chips_bet <= 50 and to_call <= 40:
                return Action.raise_by(20)
            return Action.call() if to_call > 0 else Action.check()
        else:
            if to_call > 0 and to_call < 20 and (state.my_player.chips_bet <= 20 or confidence >= 20):
                return Action.call() 
            elif to_call > 0:
                return Action.fold()
            else:
                return Action.check()
            

    elif (len(communityCards)) == 4:
        confidence = 10*numPairs + max(pairs, default=0) + 50*numTriples + 100*numQuads + (100 if numInStraight >= 5 else (10 if numInStraight == 4 else 0)) + (100 if numSameSuit >= 5 else (12 if numSameSuit == 4 and (cardSuits[0] == cardSuits[1] or highestSuitInHand >= 10) else 0))
        
        if (confidence <10):
            return Action.check() if to_call == 0 else Action.fold()
        elif (confidence >= 50):
            if True: #  (state.my_player.chips_bet <= 50):
                if(state.chips_in_pot // 2 <= 50):
                    return Action.raise_by(50)
                else:
                    return Action.raise_by(state.chips_in_pot // 2)
        elif (confidence >= 20):
            if state.my_player.chips_bet <= 50 and to_call <= 40:
                    return Action.raise_by(20)
            return Action.call() if to_call > 0 else Action.check()
        else:
            if to_call > 0 and to_call < 20 and (state.my_player.chips_bet <= 20 or confidence >= 20):
                return Action.call() 
            elif to_call > 0:
                return Action.fold()
            else:
                return Action.check()

    elif (len(communityCards)) == 5:
        confidence = 10*numPairs + max(pairs, default=0) + 50*numTriples + 100*numQuads + (100 if numInStraight >= 5 else 0) + (100 if numSameSuit >= 5 else 0)
        # print(confidence)

        if (confidence <10):
            return Action.check() if to_call == 0 else Action.fold()
        elif (confidence >= 50):
            if True: #  (state.my_player.chips_bet <= 50):
                if(state.chips_in_pot // 2 <= 50):
                    return Action.raise_by(50)
                else:
                    return Action.raise_by(state.chips_in_pot // 2)
        elif (confidence >= 20):
            if state.my_player.chips_bet <= 50 and to_call <= 40:
                return Action.raise_by(20)
            return Action.call() if to_call > 0 else Action.check()
        else:
            if to_call > 0 and to_call < 20 and (state.my_player.chips_bet <= 20 or confidence >= 20):
                return Action.call() 
            elif to_call > 0:
                return Action.fold()
            else:
                return Action.check()

    else:
        print('error, exceeded turn numbers')

    # print('bro')
    return defaultAI(state)


def defaultAI(state: GameState) -> Action: # This ai runs if myAI raises an exception, returns an invalid action or takes too long
    return Action.check() if state.my_player.chips_bet == max(player.chips_bet for player in state.players) else Action.fold()
