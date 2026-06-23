"""
Bot 'Random' para o jogo de dominó

Este módulo implementa um bot chamado 'Random' para o jogo de dominó.
O bot 'Random' seleciona aleatoriamente uma jogada dentre todos os movimentos válidos.
Caso não haja movimentos válidos, passa.
"""

import random

NOME_ESTUDANTE = "RANDOM"


def joga(estado):

    jogadas = []

    for lado in ["esquerda", "direita"]:
        for peca in estado["movimentos_validos"][lado]:
            jogadas.append({
                "jogada": "joga",
                "peca": peca,
                "lado": lado,
            })

    if len(jogadas) == 0:
        return {
            "jogada": "passa"
        }

    return random.choice(jogadas)
