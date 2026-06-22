"""
Motor do jogo de dominó de duplas

Este módulo implementa o motor do jogo de dominó de duplas.
Ele controla o fluxo de uma partida, chamando os bots das duplas, analisando e executando os movimentos selecionados.
"""

import random as r
import sys
import time
import bot_dupla_simples as bot_dupla_0
import bot_base as bot_dupla_1


def construir_domino():
    domino = []

    for a in range(7):
        for b in range(a, 7):
            domino.append((a, b))

    return domino


def relacao_equiv(peca):
    if not isinstance(peca, (list, tuple)) or len(peca) != 2:
        raise ValueError(f"peça inválida: {peca!r}")

    a = int(peca[0])
    b = int(peca[1])

    if not (0 <= a <= 6 and 0 <= b <= 6):
        raise ValueError(f"peça fora do formato: {peca!r}")

    if a <= b:
        return (a, b)

    return (b, a)


def ponto_peca(peca):
    return peca[0] + peca[1]


def is_bucha(peca):
    return peca[0] == peca[1]


def time_de(jogador):
    return jogador % 2


def parceiro_de(jogador):
    return (jogador + 2) % 4


def time_oponente(time):
    return 1 - time


def final_da_mesa(mesa):
    if not mesa:
        return None, None

    return mesa[0][0], mesa[-1][1]


def pode_jogar_esquerda(peca, mesa):
    esquerda, _ = final_da_mesa(mesa)

    if esquerda is None:
        return True

    return peca[0] == esquerda or peca[1] == esquerda


def pode_jogar_direita(peca, mesa):
    _, direita = final_da_mesa(mesa)

    if direita is None:
        return True

    return peca[0] == direita or peca[1] == direita


def oriente_esquerda(peca, esquerda_end):
    a, b = peca

    if b == esquerda_end:
        return (a, b)

    if a == esquerda_end:
        return (b, a)

    raise ValueError(f"a peça {peca} não encaixa na esquerda {esquerda_end}")


def oriente_direita(peca, direita_end):
    a, b = peca

    if a == direita_end:
        return (a, b)

    if b == direita_end:
        return (b, a)

    raise ValueError(f"a peça {peca} não encaixa na direita {direita_end}")


def movimentos_validos_por_lado(mao, mesa):
    movimentos_esquerda = []
    movimentos_direita = []

    for peca in sorted(mao):
        if pode_jogar_esquerda(peca, mesa):
            movimentos_esquerda.append(peca)

        if pode_jogar_direita(peca, mesa):
            movimentos_direita.append(peca)

    return {"esquerda": movimentos_esquerda, "direita": movimentos_direita}


def tem_algum_movimento(mao, mesa):
    movimentos = movimentos_validos_por_lado(mao, mesa)

    return bool(movimentos["esquerda"] or movimentos["direita"])


def pontos_na_mao(mao):
    return sum(ponto_peca(peca) for peca in mao)


def pontos_na_mao_do_time(maos, time):
    return pontos_na_mao(maos[time]) + pontos_na_mao(maos[time + 2])


def jogo_fechado(maos, mesa):
    for mao in maos:
        if tem_algum_movimento(mao, mesa):
            return False

    return True


def criar_estados_pros_bots(engine, jogador, rodada, turno, maos, mesa, passes_em_sequencia):
    esquerda, direita = final_da_mesa(mesa)
    movimentos_validos = movimentos_validos_por_lado(maos[jogador], mesa)

    return {
        "jogador": jogador,
        "time": time_de(jogador),
        "parceiro": parceiro_de(jogador),
        "rodada": rodada,
        "turno": turno,
        "pontuacoes": list(engine["pontuacoes"]),
        "mao": sorted(maos[jogador]),
        "mesa": list(mesa),
        "esquerda_end": esquerda,
        "direita_end": direita,
        "movimentos_validos": movimentos_validos,
        "historico": list(engine["historico"]),
        "passes_em_sequencia": passes_em_sequencia,
    }


def criar_evento(
    rodada,
    turno,
    jogador,
    jogada,
    peca=None,
    peca_orientada=None,
    lado=None,
    mesa=None,
    pontuacoes=None,
    detalhes="",
):
    esquerda, direita = final_da_mesa(mesa or [])

    if jogador is None:
        time = None
    else:
        time = time_de(jogador)

    return {
        "rodada": rodada,
        "turno": turno,
        "jogador": jogador,
        "time": time,
        "jogada": jogada,
        "peca": peca,
        "peca_orientada": peca_orientada,
        "lado": lado,
        "mesa_esquerda": esquerda,
        "mesa_direita": direita,
        "pontuacoes": list(pontuacoes or [0, 0]),
        "detalhes": detalhes,
    }


def registro_evento(engine, evento):
    engine["historico"].append(evento)

    if engine["historic"]:
        print(
            f"[r{evento['rodada']:02d} t{evento['turno']:03d}] "
            f"J{evento['jogador']} D{evento['time']} {evento['jogada']}: {evento['detalhes']}"
        )


def criar_resultado_da_rodada(time_vencedor, pontos, tipo, detalhes):
    return {
        "time_vencedor": time_vencedor,
        "pontos": pontos,
        "tipo": tipo,
        "detalhes": detalhes,
    }


def criar_jogada_ajustada(jogada, peca=None, lado=None):
    return {
        "jogada": jogada,
        "peca": peca,
        "lado": lado,
    }


def ajustar_jogada(raw):
    if not isinstance(raw, dict):
        raise ValueError("A jogada deve ser um dicionário.")

    jogada = raw.get("jogada")

    if jogada == "passa":
        return {
            "jogada": "passa",
            "peca": None,
            "lado": None,
        }

    if jogada != "joga":
        raise ValueError("A ação deve ser 'joga' ou 'passa'.")

    peca = relacao_equiv(raw["peca"])
    lado = raw["lado"]

    if lado not in {"esquerda", "direita"}:
        raise ValueError("O lado deve ser 'esquerda' ou 'direita'.")

    return {
        "jogada": "joga",
        "peca": peca,
        "lado": lado,
    }


def distribuir_pecas():
    while True:
        domino = construir_domino()
        r.shuffle(domino)

        maos = []

        for jogador in range(4):
            mao = set(domino[7 * jogador: 7 * (jogador + 1)])
            maos.append(mao)

        algum_jogador_tem_5_buchas = False

        for mao in maos:
            qtd_de_bucha = sum(1 for peca in mao if is_bucha(peca))
            if qtd_de_bucha >= 5:
                algum_jogador_tem_5_buchas = True
                break

        if not algum_jogador_tem_5_buchas:
            return maos


def colocar_peca(mesa, peca, lado):
    esquerda, direita = final_da_mesa(mesa)

    if esquerda is None or direita is None:
        mesa.append(peca)

        return peca

    if lado == "esquerda":
        orientado = oriente_esquerda(peca, esquerda)
        mesa.insert(0, orientado)

        return orientado

    if lado == "direita":
        orientado = oriente_direita(peca, direita)
        mesa.append(orientado)

        return orientado

    raise ValueError(f"lado inválido: {lado}")


def quantidade_de_pecas_jogaveis(maos, mesa):
    quantidade = 0

    for mao in maos:
        for peca in mao:
            if pode_jogar_direita(peca, mesa) or pode_jogar_esquerda(peca, mesa):
                quantidade += 1

    return quantidade


def condicao_de_batida(peca, mesa_antes, maos_antes):
    esquerda, direita = final_da_mesa(mesa_antes)

    if esquerda is None or direita is None:
        return "seca", 1

    satisfaz_esquerda = peca[0] == esquerda or peca[1] == esquerda
    satisfaz_direita = peca[0] == direita or peca[1] == direita
    satisfaz_ambos = satisfaz_esquerda and satisfaz_direita

    batida_presa = quantidade_de_pecas_jogaveis(maos_antes, mesa_antes) == 1

    if is_bucha(peca):
        if batida_presa:
            return "bicicleta", 4
        return "buchada", 2

    if satisfaz_ambos and esquerda != direita:
        if batida_presa:
            return "lasquine_preso", 3
        return "lasquine", 2

    return "seca", 1


def resultado_de_jogo_fechado(maos, fechado_pelo_jogador, pelas_pontas, engine):
    t0 = pontos_na_mao_do_time(maos, 0)
    t1 = pontos_na_mao_do_time(maos, 1)

    time_que_fechou = time_de(fechado_pelo_jogador)

    if pelas_pontas:
        if t0 == t1:
            engine["multiplicador_seca"] = 2

            return criar_resultado_da_rodada(
                None,
                0,
                "fechado_pelas_pontas_e_empate",
                "jogo fechado pelas pontas com empate; ninguém pontua e a próxima batida seca vale dobrado",
            )

        if t0 < t1:
            vencedor = 0
        else:
            vencedor = 1

        return criar_resultado_da_rodada(
            vencedor,
            1,
            "fechado_pelas_pontas",
            f"jogo fechado pelas pontas; soma D0={t0}, D1={t1}",
        )

    if t0 == t1:
        vencedor = time_oponente(time_que_fechou)

        return criar_resultado_da_rodada(
            vencedor,
            2,
            "fechado_e_empatado",
            f"jogo fechado com empate D0={t0}, D1={t1}; empate contra D{time_que_fechou}",
        )

    if t0 < t1:
        time_menor_pontos = 0
    else:
        time_menor_pontos = 1

    if time_menor_pontos == time_que_fechou:
        return criar_resultado_da_rodada(
            time_menor_pontos,
            1,
            "fechado_e_vencedor_quem_fechou",
            f"jogo fechado; D{time_menor_pontos} fechou e tem menor soma; D0={t0}, D1={t1}",
        )

    return criar_resultado_da_rodada(
        time_menor_pontos,
        2,
        "fechado_e_perdedor_quem_fechou",
        f"jogo fechado; D{time_que_fechou} fechou, mas D{time_menor_pontos} tem menor soma; D0={t0}, D1={t1}",
    )


def resultado_por_penalidade(time_penalizado, reason):
    return criar_resultado_da_rodada(
        time_oponente(time_penalizado),
        2,
        "penalidade",
        reason,
    )


def aplicar_pontuacao(engine, resultado):
    vencedor = resultado["time_vencedor"]
    pontos = resultado["pontos"]
    tipo = resultado["tipo"]

    if vencedor is None or pontos <= 0:
        if tipo != "seca":
            engine["time_do_japao"] = None
            engine["ofensiva_japao"] = 0

        return

    if tipo == "seca":
        pontos *= engine["multiplicador_seca"]
        engine["multiplicador_seca"] = 1

        if engine["time_do_japao"] is None:
            if engine["pontuacoes"] == [3, 0]:
                engine["time_do_japao"] = 1
                engine["ofensiva_japao"] = 0
            elif engine["pontuacoes"] == [0, 3]:
                engine["time_do_japao"] = 0
                engine["ofensiva_japao"] = 0

        if engine["time_do_japao"] == vencedor:
            engine["ofensiva_japao"] += 1

            if engine["ofensiva_japao"] == 3:
                pontos = 2
                engine["time_do_japao"] = None
                engine["ofensiva_japao"] = 0
        else:
            engine["time_do_japao"] = None
            engine["ofensiva_japao"] = 0

    else:
        engine["time_do_japao"] = None
        engine["ofensiva_japao"] = 0
        engine["multiplicador_seca"] = 1

    engine["pontuacoes"][vencedor] += pontos


def executar_com_timeout(func, estado, timeout=0.1):
    """
    Executa a função do bot sob vigilância do interpretador (sem criar processos).
    Se o bot entrar em loop infinito ou demorar, a execução é abortada.
    """
    inicio = time.time()

    def tracer(frame, event, arg):
        # A cada linha de código que o bot do aluno executa, essa verificação roda
        if time.time() - inicio > timeout:
            # Se estourar o tempo, levanta o erro e interrompe a execução do aluno imediatamente
            raise TimeoutError("Tempo limite de 1 segundo excedido (Loop Infinito ou lentidão).")
        return tracer

    # Liga o "cronômetro"
    sys.settrace(tracer)

    try:
        # Chama a função do aluno
        resultado = func(estado)
        return resultado
    finally:
        # DESLIGA o vigilante assim que o aluno retorna a resposta
        sys.settrace(None)


def jogar_rodada(engine, rodada):
    maos = distribuir_pecas()
    mesa = []
    peca_que_comeca = (engine["bucha_comecando"], engine["bucha_comecando"])
    primeiro = None

    for jogador in range(4):
        if peca_que_comeca in maos[jogador]:
            primeiro = jogador
            break

    if primeiro is None:
        raise RuntimeError(f"peça inicial {peca_que_comeca} não encontrada")

    maos[primeiro].remove(peca_que_comeca)
    mesa.append(peca_que_comeca)

    jogador_do_turno = (primeiro + 1) % 4
    ultimo_jogador = primeiro
    passes_em_sequencia = 0
    turno = 0

    registro_evento(
        engine,
        criar_evento(
            rodada=rodada,
            turno=turno,
            jogador=primeiro,
            jogada="comeco",
            peca=peca_que_comeca,
            peca_orientada=peca_que_comeca,
            lado="comeco",
            mesa=mesa,
            pontuacoes=engine["pontuacoes"],
            detalhes=f"J{primeiro} inicia com {peca_que_comeca}",
        ),
    )

    while True:
        turno += 1

        estado = criar_estados_pros_bots(
            engine=engine,
            jogador=jogador_do_turno,
            rodada=rodada,
            turno=turno,
            maos=maos,
            mesa=mesa,
            passes_em_sequencia=passes_em_sequencia,
        )

        bot = engine["time_bots"][time_de(jogador_do_turno)]

        try:
            # Executa com limite de 0.1 segundo
            raw_jogada = executar_com_timeout(bot, estado, timeout=0.1)
            jogada = ajustar_jogada(raw_jogada)

        except TimeoutError as e:
            detalhes = str(e)
            registro_evento(
                engine,
                criar_evento(
                    rodada=rodada, turno=turno, jogador=jogador_do_turno,
                    jogada="timeout_estouro_de_tempo", mesa=mesa,
                    pontuacoes=engine["pontuacoes"], detalhes=detalhes
                )
            )
            # Aborta a partida inteira e avisa ao torneio quem falhou
            raise RuntimeError(f"WO_TIME_{time_de(jogador_do_turno)}") from e

        except Exception as e:
            # Captura caso o aluno tenha submetido um código com erro de sintaxe/lógica
            detalhes = f"O bot quebrou durante a execução: {type(e).__name__} - {str(e)}"
            registro_evento(
                engine,
                criar_evento(
                    rodada=rodada, turno=turno, jogador=jogador_do_turno,
                    jogada="erro_de_execucao", mesa=mesa,
                    pontuacoes=engine["pontuacoes"], detalhes=detalhes
                )
            )
            # Aborta a partida inteira e avisa ao torneio quem falhou
            raise RuntimeError(f"WO_TIME_{time_de(jogador_do_turno)}") from e

        if jogada["jogada"] == "passa":
            if tem_algum_movimento(maos[jogador_do_turno], mesa):
                detalhes = "passou tendo peça jogável"

                registro_evento(
                    engine,
                    criar_evento(
                        rodada=rodada,
                        turno=turno,
                        jogador=jogador_do_turno,
                        jogada="passou_com_peca_na_mao",
                        mesa=mesa,
                        pontuacoes=engine["pontuacoes"],
                        detalhes=detalhes,
                    ),
                )

                return resultado_por_penalidade(time_de(jogador_do_turno), detalhes)

            passes_em_sequencia += 1

            registro_evento(
                engine,
                criar_evento(
                    rodada=rodada,
                    turno=turno,
                    jogador=jogador_do_turno,
                    jogada="passo",
                    mesa=mesa,
                    pontuacoes=engine["pontuacoes"],
                    detalhes="passe válido",
                ),
            )

            if passes_em_sequencia >= 4:
                return resultado_de_jogo_fechado(
                    maos=maos,
                    fechado_pelo_jogador=ultimo_jogador,
                    pelas_pontas=False,
                    engine=engine,
                )

            jogador_do_turno = (jogador_do_turno + 1) % 4
            continue

        peca = jogada["peca"]
        lado = jogada["lado"]

        if peca not in maos[jogador_do_turno]:
            detalhes = f"tentou jogar {peca}, mas essa peça não está na própria mão"

            registro_evento(
                engine,
                criar_evento(
                    rodada=rodada,
                    turno=turno,
                    jogador=jogador_do_turno,
                    jogada="peca_invalida",
                    peca=peca,
                    mesa=mesa,
                    pontuacoes=engine["pontuacoes"],
                    detalhes=detalhes,
                ),
            )

            return resultado_por_penalidade(time_de(jogador_do_turno), detalhes)

        esquerda_ok = pode_jogar_esquerda(peca, mesa)
        direita_ok = pode_jogar_direita(peca, mesa)

        if not esquerda_ok and not direita_ok:
            detalhes = f"gato: peça {peca} não encaixa em nenhuma ponta"

            registro_evento(
                engine,
                criar_evento(
                    rodada=rodada,
                    turno=turno,
                    jogador=jogador_do_turno,
                    jogada="gato",
                    peca=peca,
                    mesa=mesa,
                    pontuacoes=engine["pontuacoes"],
                    detalhes=detalhes,
                ),
            )

            return resultado_por_penalidade(time_de(jogador_do_turno), detalhes)

        requested_lado = lado

        if lado == "esquerda" and not esquerda_ok and direita_ok:
            lado = "direita"
            correction = "lado corrigido: a peça não encaixava à esquerda, mas encaixava à direita"
        elif lado == "direita" and not direita_ok and esquerda_ok:
            lado = "esquerda"
            correction = "lado corrigido: a peça não encaixava à direita, mas encaixava à esquerda"
        else:
            correction = ""

        if lado is None:
            detalhes = f"gato: peça {peca} não encaixa em nenhuma ponta"

            registro_evento(
                engine,
                criar_evento(
                    rodada=rodada,
                    turno=turno,
                    jogador=jogador_do_turno,
                    jogada="gato",
                    peca=peca,
                    mesa=mesa,
                    pontuacoes=engine["pontuacoes"],
                    detalhes=detalhes,
                ),
            )

            return resultado_por_penalidade(time_de(jogador_do_turno), detalhes)

        mesa_antes = list(mesa)
        maos_antes = [set(mao) for mao in maos]

        peca_orientada = colocar_peca(mesa, peca, lado)
        maos[jogador_do_turno].remove(peca)

        passes_em_sequencia = 0
        ultimo_jogador = jogador_do_turno

        if requested_lado != lado and requested_lado is not None:
            detalhes = f"J{jogador_do_turno} jogou {peca} na {lado}. {correction}"
        else:
            detalhes = f"J{jogador_do_turno} jogou {peca} na {lado}"

        registro_evento(
            engine,
            criar_evento(
                rodada=rodada,
                turno=turno,
                jogador=jogador_do_turno,
                jogada="joga",
                peca=peca,
                peca_orientada=peca_orientada,
                lado=lado,
                mesa=mesa,
                pontuacoes=engine["pontuacoes"],
                detalhes=detalhes,
            ),
        )

        if len(maos[jogador_do_turno]) == 0:
            tipo, pontos = condicao_de_batida(peca, mesa_antes, maos_antes)

            return criar_resultado_da_rodada(
                time_vencedor=time_de(jogador_do_turno),
                pontos=pontos,
                tipo=tipo,
                detalhes=f"J{jogador_do_turno} bateu; tipo={tipo}; pontos={pontos}",
            )

        if jogo_fechado(maos, mesa):
            return resultado_de_jogo_fechado(
                maos=maos,
                fechado_pelo_jogador=jogador_do_turno,
                pelas_pontas=True,
                engine=engine,
            )

        jogador_do_turno = (jogador_do_turno + 1) % 4


def criar_engine(bot0, bot1, nome0, nome1, seed=None, target_score=4, historic=False):
    if seed is not None:
        r.seed(seed)

    return {
        "time_bots": [bot0, bot1],
        "nomes_time": [nome0, nome1],
        "target_score": target_score,
        "historic": historic,
        "pontuacoes": [0, 0],
        "historico": [],
        "resultados_da_rodada": [],
        "bucha_comecando": 6,
        "multiplicador_seca": 1,
        "time_do_japao": None,
        "ofensiva_japao": 0,
    }


def jogar_partida(engine):
    rodada = 0

    while max(engine["pontuacoes"]) < engine["target_score"]:
        rodada += 1

        resultado = jogar_rodada(engine, rodada)

        aplicar_pontuacao(engine, resultado)

        engine["resultados_da_rodada"].append(dict(resultado))

        registro_evento(
            engine,
            criar_evento(
                rodada=rodada,
                turno=-1,
                jogador=None,
                jogada="fim_da_rodada",
                mesa=[],
                pontuacoes=engine["pontuacoes"],
                detalhes=f"resultado={resultado}; placar={engine['pontuacoes']}",
            ),
        )

        engine["bucha_comecando"] = (engine["bucha_comecando"] - 1) % 7

    if engine["pontuacoes"][0] >= engine["pontuacoes"][1]:
        vencedor = 0
    else:
        vencedor = 1

    return {
        "time_vencedor": vencedor,
        "pontuacoes": list(engine["pontuacoes"]),
        "rodadas": rodada,
        "resultados_da_rodada": list(engine["resultados_da_rodada"]),
        "historico": list(engine["historico"]),
    }


def jogo():
    seed = None
    target_score = 50
    historic = True

    bot0 = bot_dupla_0.joga
    bot1 = bot_dupla_1.joga

    nome0 = bot_dupla_0.NOME_ESTUDANTE
    nome1 = bot_dupla_1.NOME_ESTUDANTE

    engine = criar_engine(
        bot0=bot0,
        bot1=bot1,
        nome0=nome0,
        nome1=nome1,
        seed=seed,
        target_score=target_score,
        historic=historic,
    )

    resultado = jogar_partida(engine)

    print("Resultado final")
    time_vencedor = resultado["time_vencedor"]
    nome_vencedor = engine["nomes_time"][time_vencedor]
    print(f"Dupla vencedora: {time_vencedor} - {nome_vencedor}")
    print(f"Placar final: {engine['nomes_time'][0]} {resultado['pontuacoes'][0]} x " +
          f"{resultado['pontuacoes'][1]} {engine['nomes_time'][1]}")
    print(f"Total de jogos: {resultado['rodadas']}")


if __name__ == '__main__':
    jogo()
