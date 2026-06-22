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

    if side == "esquerda":
        newLeftEnd = tile[1] if tile[0] == leftEnd else tile[0]
        qualityValue = resultedSuits[newLeftEnd] + resultedSuits[rightEnd]
    else:
        newRightEnd = tile[1] if tile[0] == rightEnd else tile[0]
        qualityValue = resultedSuits[leftEnd] + resultedSuits[newRightEnd]

    return stdNormalize(qualityValue, 0, 9)

def hfDumpDoubles(move,gameData):
    if move[0][0] == move[0][1]:
        return 1
    return 0

def hfMinimizeHandWeight(move,gameData):
    qualityValue = move[0][0] + move[0][1]
    
    return stdNormalize(qualityValue, 0, 12)

def hfCloseGame(move, gameData):
    if gameData["handSize"] == 1:
        return 1
    return 0

hfFunctions = [
    hfHandBalancing,
    hfBoardControl,
    hfDumpDoubles,
    hfMinimizeHandWeight,
    hfCloseGame
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
# DATA CLEANING
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

    return {
        "gameState": gameState,
        "availableMoves": turnMovesInArray(gameState["movimentos_validos"]),
        "playerHand": hand,
        "currentSuits": countSuits(hand),
        "handSize": len(hand),
        "boardEnds": (gameState["esquerda_end"], gameState["direita_end"])
    }

# ===========================
# CARD COUNTING
# ===========================
def countSuits(hand):
    numSuits = [0]*7

    for tile in hand:
        numSuits[tile[0]] += 1
        numSuits[tile[1]] += 1
    
    return numSuits