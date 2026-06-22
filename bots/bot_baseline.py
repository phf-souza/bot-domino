NOME_ESTUDANTE = "Pedro Souza"

# ===========================
# GLOBAL CONSTANTS
# ===========================
ALL_TILES = { (i, j) for i in range(7) for j in range(i, 7) }

SUIT_SETS = {
    suit: { (min(suit, j), max(suit, j)) for j in range(7) }
    for suit in range(7)
}

RELATIVE_IDS = {
    0: "me",
    1: "rightOpponent",
    2: "partner",
    3: "leftOpponent"
}

# ===========================
# "JOGA" FUNCTION
# ===========================
def joga(estado):
    numMoves = countMoves(estado["movimentos_validos"])
    
    if  numMoves == 0:
        return {
            "jogada": "passa"
        }
    
    elif numMoves == 1:
        return onlyMove(estado["movimentos_validos"])

    return bestMove(estado)


# ===========================
# DEGENERATE CASES
# ===========================
def countMoves(validMoves):         
    return len(validMoves["esquerda"]) + len(validMoves["direita"])


def onlyMove(validMoves):
    if len(validMoves["esquerda"]) == 0:
        position = "direita"
    else:
        position = "esquerda"

    return {
        "jogada": "joga",
        "peca": validMoves[position][0],
        "lado": position
    }


# ===========================
# HEURISTIC FUNCTIONS
# ===========================
def hfHandBalancing(move,gameData):
    resultedSuits = suitsAfterMove(move, gameData["currentSuits"])
    qualityValue = 7 - resultedSuits.count(0) 
    
    return stdNormalize(qualityValue, 0, 7)

def hfBoardControl(move,gameData):
    resultedSuits = suitsAfterMove(move, gameData["currentSuits"])
    leftEnd, rightEnd = gameData["boardEnds"]
    tile, side = move

    if leftEnd is None or rightEnd is None:
        newLeftEnd, newRightEnd = tile[0], tile[1]
    elif side == "esquerda":
        newLeftEnd = tile[1] if tile[0] == leftEnd else tile[0]
        qualityValue = resultedSuits[newLeftEnd] + resultedSuits[rightEnd]
    else:
        newRightEnd = tile[1] if tile[0] == rightEnd else tile[0]
        qualityValue = resultedSuits[leftEnd] + resultedSuits[newRightEnd]

    return stdNormalize(qualityValue, 0, 12)

def hfDumpDoubles(move,gameData):
    if move[0][0] == move[0][1]:
        return 1
    return 0

def hfMinimizeHandWeight(move,gameData):
    qualityValue = move[0][0] + move[0][1]
    
    return stdNormalize(qualityValue, 0, 12)

def hfCloseGame(move, gameData):
    if gameData["handSize"] > 1:
        return 0
    
    points = 1
    
    tile, side = move
    leftEnd, rightEnd = gameData["boardEnds"]

    isDouble = tile[0] == tile[1]
    fitsLeft = (tile[0] == leftEnd) or (tile[1] == leftEnd)
    fitsRight = (tile[0] == rightEnd) or (tile[1] == rightEnd)
    isLasquine = (not isDouble) and fitsLeft and fitsRight

    if isDouble:
        if gameData["isPresa"]:
            # bicicleta/buchada presa
            points = 4
        else:
            # buchada
            points = 2
    
    elif isLasquine:
        if gameData["isPresa"]:
            # lasquine preso
            points = 3
        else:
            #lasquine
            points = 2
    
    return stdNormalize(points, 0, 4)

def hfStarvationRight(move, gameData):
    newLeft, newRight = getNewEnds(move, gameData["boardEnds"])
    counts = gameData["opponentSuits"]["rightOpponent"]
    return stdNormalize(14 - getSuitCount(newLeft, newRight, counts), 0, 14)

def hfStarvationLeft(move, gameData):
    newLeft, newRight = getNewEnds(move, gameData["boardEnds"])
    counts = gameData["opponentSuits"]["leftOpponent"]
    return stdNormalize(14 - getSuitCount(newLeft, newRight, counts), 0, 14)

def hfPartnerSupport(move, gameData):
    newLeft, newRight = getNewEnds(move, gameData["boardEnds"])
    counts = gameData["opponentSuits"]["partner"]
    return stdNormalize(getSuitCount(newLeft, newRight, counts), 0, 14)


hfFunctions = [
    hfHandBalancing,
    hfBoardControl,
    hfDumpDoubles,
    hfMinimizeHandWeight,
    hfCloseGame,
    hfStarvationRight,
    hfStarvationLeft,
    hfPartnerSupport
]


# ===========================
# CONDITIONAL WEIGHT FUNCTION
# ===========================
def weightFunction(gameState):
    return [1]*len(hfFunctions)


# ===========================
# QUALITY MOVE CALCULATOR
# ===========================
def bestMove(gameState):
    gameData = gameStateToData(gameState)
    currentWeight = weightFunction(gameData["gameState"])

    bestMoveTuple = max(gameData["availableMoves"], key=lambda move: hfSum(move, currentWeight, gameData))

    return {
        "jogada": "joga",
        "peca": bestMoveTuple[0],
        "lado": bestMoveTuple[1]
    }

def turnMovesInArray(validMoves):
    # move[0] = tile, move[1] = side
    movesArray = []

    for position in validMoves:
        for tile in validMoves[position]:
            movesArray.append((tile, position))
    
    return movesArray
 
def hfSum(move, weightList, gameData):
    qualityValue = 0

    for index, hf in enumerate(hfFunctions):
        qualityValue += weightList[index]*hf(move, gameData)
    
    return qualityValue


# ===========================
# DATA CLEANING & HELPER FUNCTIONS
# ===========================
def suitsAfterMove(move, currentSuits):
    expectedSuits = currentSuits.copy()
    expectedSuits[move[0][0]] -= 1
    expectedSuits[move[0][1]] -= 1

    return expectedSuits

def stdNormalize(value, min, max):
    return (value-min)/(max-min)

def gameStateToData(gameState):
    hand = gameState["mao"]
    boardEnds = (gameState["esquerda_end"], gameState["direita_end"])
    tableSet = set(gameState["mesa"])
    handSize = len(hand)

    round = gameState["rodada"]
    myId = gameState["jogador"]
    #scores = gameState["pontuacoes"]
    #myTeam = gameState["time"]
    history = gameState["historico"]

    oppPossibilities = buildInferenceEngine(
            hand, 
            history, 
            round, 
            myId
        )

    oppSuitCounts = {
        player: {suit: len(oppPossibilities[player] & SUIT_SETS[suit]) for suit in range(7)}
        for player in oppPossibilities
    }

    return {
        "gameState": gameState,
        "availableMoves": turnMovesInArray(gameState["movimentos_validos"]),
        "playerHand": hand,
        "currentSuits": countSuits(hand),
        "handSize": handSize,
        "boardEnds": boardEnds,
        "tableSet": tableSet,
        "isPresa": isPresa(boardEnds, tableSet) if handSize == 1 else False,

        "round": gameState["rodada"],
        "myId": gameState["jogador"],
        "scores": gameState["pontuacoes"],
        "myTeam": gameState["time"],

        "opponentPossibilities": oppPossibilities,
        "opponentSuits": oppSuitCounts
    }

def isPresa(boardEnds, table):
    leftEnd, rightEnd = boardEnds
    remainingTiles = ALL_TILES - table
    playableTiles = SUIT_SETS[leftEnd] | SUIT_SETS[rightEnd]
    validUnplayedTiles = remainingTiles & playableTiles

    return len(validUnplayedTiles) == 1

def getNewEnds(move, boardEnds):
    tile, side = move
    leftEnd, rightEnd = boardEnds

    if leftEnd is None or rightEnd is None:
        return [tile[0], tile[1]]

    if side == "esquerda":
        return [tile[0] if tile[1] == leftEnd else tile[1] ,rightEnd]
    
    return [leftEnd, tile[0] if tile[1] == rightEnd else tile[1]]

# ===========================
# CARD COUNTING
# ===========================
def countSuits(hand):
    numSuits = [0]*7

    for tile in hand:
        numSuits[tile[0]] += 1
        numSuits[tile[1]] += 1
    
    return numSuits

def getSuitCount(newLeft, newRight, suitCounts):
    if newLeft == newRight:
        return suitCounts[newLeft]
    return suitCounts[newLeft] + suitCounts[newRight]

# ===========================
# INFERENCE ENGINE
# ===========================

def buildInferenceEngine(hand, history, currentRound, myId):
    normalizedHand = { (min(t), max(t)) for t in hand }
    unseenTiles = ALL_TILES - normalizedHand
    
    possibleTiles = {
        "leftOpponent": unseenTiles.copy(),
        "partner": unseenTiles.copy(),
        "rightOpponent": unseenTiles.copy()
    }

    leftEnd = None
    rightEnd = None

    for event in history:
        if event["rodada"] != currentRound:
            continue

        relativePlayer = getRelativePlayer(myId, event["jogador"])

        if event["jogada"] == "joga":
            raw_tile = event["peca"]
            tile = (min(raw_tile), max(raw_tile))
            side = event["lado"]

            if relativePlayer != "me":
                possibleTiles["leftOpponent"].discard(tile)
                possibleTiles["partner"].discard(tile)
                possibleTiles["rightOpponent"].discard(tile)
            
            if leftEnd is None:
                leftEnd = tile[0]
                rightEnd = tile[1]
            elif side == "esquerda":
                leftEnd = tile[1] if tile[0] == leftEnd else tile[0]
            else:
                rightEnd = tile[1] if tile[0] == rightEnd else tile[0]

        elif event["jogada"] == "passa":        
            if relativePlayer != "me":
                if leftEnd is not None:
                    activeSuits = SUIT_SETS[leftEnd] | SUIT_SETS[rightEnd]
                    possibleTiles[relativePlayer] -= activeSuits
        
    return possibleTiles


def getRelativePlayer(myId, playerId):
    return RELATIVE_IDS[(playerId-myId)%4] 