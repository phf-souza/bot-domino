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
def hfHandBalancing():
    return 0

def hfBoardControl():
    return 0

def hfDumpDoubles():
    return 0

def hfMinimizeHandWeight():
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
def weightFunction():
    return [1]*len(hfFunctions)


# ===========================
# QUALITY MOVE CALCULATOR
# ===========================
def bestMove(gameState):
    avaliableMoves = turnMovesInArray(gameState["movimentos_validos"])
    moveQuality = []

    for move in avaliableMoves:
        moveQuality.append(hfSum(move,gameState))
    
    bestMoveIndex = moveQuality.index(max(moveQuality))

    return {
        "jogada": "joga",
        "peca": avaliableMoves[bestMoveIndex]["tile"],
        "lado": avaliableMoves[bestMoveIndex]["side"]
    }

def turnMovesInArray(validMoves):
    movesArray = []

    for position in validMoves:
        for tile in validMoves[position]:
            movesArray.append({
                "tile": tile,
                "side": position
            })
    
    return movesArray
git 
def hfSum(move, gameState):
    weightList = weightFunction()
    numHfFunctions = len(weightList)
    qualityValue = 0

    gameData = gameState

    for index in range(numHfFunctions):
        qualityValue += weightList[index]*hfFunctions[index](move, gameState)
    
    return qualityValue