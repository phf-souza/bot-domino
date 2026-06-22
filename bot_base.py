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
# HEURISTIC FUNCTIONS
# ===========================
def hfHandBalancing(move,gameData):
    return 0

def hfBoardControl(move,gameData):
    return 0

def hfDumpDoubles(move,gameData):
    return 0

def hfMinimizeHandWeight(move,gameData):
    return 0

hfFunctions = [
    hfHandBalancing,
    hfBoardControl,
    hfDumpDoubles,
    hfMinimizeHandWeight
]


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
# CONDITIONAL WEIGHT FUNCTION
# ===========================
def weightFunction(gameState):
    return [1]*len(hfFunctions)


# ===========================
# QUALITY MOVE CALCULATOR
# ===========================
def bestMove(gameState):
    availableMoves = turnMovesInArray(gameState["movimentos_validos"])
    currentWeight = weightFunction(gameState)
    gameData = gameState

    bestMoveTuple = max(availableMoves, key=lambda move: hfSum(move, currentWeight, gameData))

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