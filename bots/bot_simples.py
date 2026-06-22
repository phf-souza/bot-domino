"""
Bot 'Simples' para o jogo de dominó

Este módulo implementa um bot chamado 'Simples' para o jogo de dominó.
O bot 'Simples' sempre seleciona a jogada correspondente ao primeiro movimento válido identificado.
Caso não haja movimentos válidos, ele passa.
"""

NOME_ESTUDANTE = "Simples"


def joga(estado):
	movimentos = estado["movimentos_validos"]
		
	if movimentos["esquerda"]:
		return {
			"jogada": "joga",
			"peca": movimentos["esquerda"][0],
			"lado": "esquerda"
		}
		
	if movimentos["direita"]:
		return {
			"jogada": "joga",
			"peca": movimentos["direita"][0],
			"lado": "direita"
		}
		
	return {
			"jogada": "passa"
		}
