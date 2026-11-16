from poker.action import Action
from poker.game_state import GameState
import math
import random

RANKS = {name: i for i, name in enumerate('one two three four five six seven eight nine ten jack queen king ace'.split(), 1)}
SUITS = ['club', 'diamond', 'heart', 'spade']
preCache = {}


def parseCard(card):
    return (RANKS[str(card.rank.value).lower()], str(card.suit.value).lower())


def straightHigh(ranks):
    ranks = set(ranks) | ({1} if 14 in ranks else set())
    return next((high for high in range(14, 4, -1) if all(high - k in ranks for k in range(5))), 0)


def evaluateHand(cards):
    counts = {}
    for rank, suit in cards:
        counts[rank] = counts.get(rank, 0) + 1
    groups = sorted(counts, key=lambda rank: (counts[rank], rank), reverse=True)
    flush = None
    for suit in SUITS:
        suited = sorted((rank for rank, s in cards if s == suit), reverse=True)
        if len(suited) >= 5:
            flush = suited
            if straightHigh(suited):
                return (8, straightHigh(suited))
    top, second = counts[groups[0]], counts[groups[1]] if len(groups) > 1 else 0
    if top == 4:
        return (7, groups[0], max(groups[1:]))
    if top == 3 and second >= 2:
        return (6, groups[0], groups[1])
    if flush:
        return (5,) + tuple(flush[:5])
    if straightHigh(groups):
        return (4, straightHigh(groups))
    if top == 3:
        return (3, groups[0]) + tuple(sorted(groups[1:], reverse=True)[:2])
    if top == 2 and second == 2:
        return (2, groups[0], groups[1], max(groups[2:]))
    if top == 2:
        return (1, groups[0]) + tuple(sorted(groups[1:], reverse=True)[:3])
    return (0,) + tuple(sorted(groups, reverse=True)[:5])


def chenScore(card1, card2):
    value = lambda rank: {14: 10, 13: 8, 12: 7, 11: 6}.get(rank, rank / 2.0)
    hi, lo = max(card1[0], card2[0]), min(card1[0], card2[0])
    if hi == lo:
        return max(5.0, 2 * value(hi))
    gap = hi - lo - 1
    score = value(hi) + (2 if card1[1] == card2[1] else 0) - {0: 0, 1: 1, 2: 2, 3: 4}.get(gap, 5)
    return float(math.ceil(score + (1 if gap <= 1 and hi < 12 else 0)))


def calcEquity(hand, board, numOpp, numSims, rangeThr=None):
    known = set(hand) | set(board)
    deck = [(rank, suit) for rank in range(2, 15) for suit in SUITS if (rank, suit) not in known]
    needBoard = 5 - len(board)
    numOpp = max(1, min(numOpp, (len(deck) - needBoard) // 2))
    score = 0.0
    for _ in range(numSims):
        need = needBoard + 2 * numOpp
        cards = random.sample(deck, max(need, 40) if rangeThr is not None else need)
        if rangeThr is not None:
            for i in range(0, 40, 2):
                if chenScore(cards[i], cards[i + 1]) >= rangeThr:
                    cards[0], cards[i] = cards[i], cards[0]
                    cards[1], cards[i + 1] = cards[i + 1], cards[1]
                    break
        drawn = cards[:need]
        fullBoard = list(board) + drawn[2 * numOpp:]
        myScore = evaluateHand(list(hand) + fullBoard)
        bestOpp = max(evaluateHand(drawn[2 * i:2 * i + 2] + fullBoard) for i in range(numOpp))
        score += 1.0 if myScore > bestOpp else 0.5 if myScore == bestOpp else 0.0
    return score / numSims


def myAI(state: GameState) -> Action:
    me = state.my_player
    bigBlind = max(state.big_blind, 1)
    hand = [parseCard(c) for c in me.hole_cards]
    board = [parseCard(c) for c in state.community_cards]
    pot = max(int(state.chips_in_pot), 0)
    maxBet = max(player.chips_bet for player in state.players)
    toCall = max(0, maxBet - me.chips_bet)
    leftAfterCalling = me.chips_in_stack - toCall
    others = [player for player in state.players if player is not me and not player.has_folded]
    canBeCalled = any(player.chips_in_stack > 0 for player in others)
    numOpp = max(1, len(others))
    totalStack = me.chips_in_stack + me.chips_bet
    bigBlinds = totalStack / bigBlind
    raised = toCall > bigBlind
    myShare = totalStack / max(sum(player.chips_in_stack + player.chips_bet for player in state.players), 1)
    requiredEquity = toCall / (pot + toCall) if toCall > 0 else 0.0

    rangeThr = None
    raiser = max(state.players, key=lambda player: player.chips_bet)
    if not board and raised and raiser is not me:
        raiserBigBlinds = (raiser.chips_in_stack + raiser.chips_bet) / bigBlind
        rangeThr = 2.0 if raiserBigBlinds < 10 else 3.0 if toCall <= 4 * bigBlind else 5.0 if toCall <= 10 * bigBlind else 7.0

    if not board and rangeThr is None:
        (rank1, suit1), (rank2, suit2) = hand
        cacheKey = (max(rank1, rank2), min(rank1, rank2), suit1 == suit2 and rank1 != rank2, numOpp)
        if cacheKey not in preCache:
            preCache[cacheKey] = calcEquity(hand, board, numOpp, 1500)
        eq = preCache[cacheKey]
    else:
        baseSims = 500 if numOpp <= 2 else 350
        eq = calcEquity(hand, board, numOpp, baseSims, rangeThr)
        if toCall > 0 and abs(eq - requiredEquity) < 0.06:
            eq = (eq * baseSims + calcEquity(hand, board, numOpp, 900, rangeThr) * 900) / (baseSims + 900)

    penalty = min(0.14, 0.04 + 0.08 * toCall / max(me.chips_in_stack, 1) + 0.08 * toCall / max(pot, 1)) if board and toCall > 0 else 0.0
    effEq = max(0.0, eq - penalty)
    ratio = effEq * (numOpp + 1)
    fair = 1.0 / (numOpp + 1)
    strength = (effEq - fair) / (1.0 - fair)

    def bet(chips):
        if leftAfterCalling <= 0 or not canBeCalled:
            return Action.check() if toCall == 0 else Action.call()
        return Action.raise_by(min(max(int(chips), bigBlind), leftAfterCalling))

    shove = bet(leftAfterCalling)

    callMargin = 0.06 if leftAfterCalling <= 0 and bigBlinds > 12 else 0.03
    if myShare >= 0.5 and toCall >= 0.3 * me.chips_in_stack:
        callMargin += 0.03
    if toCall == 0:
        fallback = Action.check()
    elif effEq > requiredEquity + callMargin and (ratio >= 1.0 or rangeThr is not None):
        fallback = Action.call()
    elif toCall <= 0.08 * (pot + toCall) and effEq >= requiredEquity:
        fallback = Action.call()
    else:
        fallback = Action.fold()

    if not board:
        if bigBlinds < 10:
            if not raised:
                return shove if bigBlinds <= 5 or ratio >= 0.9 else fallback
            if effEq > requiredEquity + 0.01:
                return Action.call() if effEq < 0.62 else shove
            return Action.fold()
        if not raised:
            if strength >= 0.5:
                return bet(4 * bigBlind - maxBet) if bigBlinds > 30 else shove
            if strength >= (0.15 if numOpp == 1 else 0.22):
                return bet(3 * bigBlind - maxBet)
            return fallback
        if effEq >= 0.66:
            return shove if bigBlinds <= 40 else bet(pot)
        return fallback

    spr = leftAfterCalling / max(pot, 1)
    if toCall == 0:
        if spr <= 1.0 and strength >= 0.3:
            return shove
        for minStrength, fraction in [(0.72, 1.0), (0.55, 0.7), (0.35, 0.45)]:
            if strength >= minStrength:
                return bet(pot * fraction)
        return fallback
    if spr <= 1.5 and effEq > requiredEquity + 0.02 and ratio >= 1.2:
        return shove if strength >= 0.45 else Action.call()
    if strength >= 0.65 and toCall <= pot:
        return bet(pot * 0.75)
    return fallback

    return defaultAI(state)


def defaultAI(state: GameState) -> Action: # This ai runs if myAI raises an exception, returns an invalid action or takes too long
    return Action.check() if not state.my_player.chips_in_stack or state.my_player.chips_bet == max(player.chips_bet for player in state.players) else Action.fold()
# Re-commit - Freddie
