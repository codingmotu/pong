# -*- coding: utf-8 -*-
"""
Jogo da Velha (Tic-Tac-Toe) - 2 jogadores no terminal
Como usar:
    python3 jogo_da_velha.py
"""

def limpar_tela():
    try:
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass

def desenhar_tabuleiro(tab):
    print("\n")
    print(f" {tab[0]} | {tab[1]} | {tab[2]} ")
    print("---+---+---")
    print(f" {tab[3]} | {tab[4]} | {tab[5]} ")
    print("---+---+---")
    print(f" {tab[6]} | {tab[7]} | {tab[8]} ")
    print("\n")

def vencedor(tab):
    linhas = [
        (0,1,2), (3,4,5), (6,7,8),  # linhas
        (0,3,6), (1,4,7), (2,5,8),  # colunas
        (0,4,8), (2,4,6)            # diagonais
    ]
    for a,b,c in linhas:
        if tab[a] == tab[b] == tab[c] and tab[a] in ("X","O"):
            return tab[a]
    if all(casa in ("X","O") for casa in tab):
        return "Empate"
    return None

def solicitar_jogada(jogador, tab):
    while True:
        try:
            pos = input(f"Jogador {jogador} - escolha uma casa (1-9): ").strip()
            if pos.lower() in ("q", "quit", "sair"):
                return None
            pos = int(pos)
            if pos < 1 or pos > 9:
                print("Valor inválido. Digite um número de 1 a 9.")
                continue
            idx = pos - 1
            if tab[idx] in ("X", "O"):
                print("Casa já ocupada. Escolha outra.")
                continue
            return idx
        except ValueError:
            print("Entrada inválida. Digite um número de 1 a 9.")

def jogar():
    while True:
        tabuleiro = [str(i) for i in range(1, 10)]
        jogador = "X"
        limpar_tela()
        print("=== Jogo da Velha ===")
        print("Digite 'q' para sair a qualquer momento.")
        desenhar_tabuleiro(tabuleiro)

        while True:
            idx = solicitar_jogada(jogador, tabuleiro)
            if idx is None:
                print("Saindo do jogo. Até mais!")
                return
            tabuleiro[idx] = jogador
            limpar_tela()
            print("=== Jogo da Velha ===")
            desenhar_tabuleiro(tabuleiro)

            res = vencedor(tabuleiro)
            if res == "X" or res == "O":
                print(f"Jogador {res} venceu!")
                break
            elif res == "Empate":
                print("Deu velha! Empate.")
                break

            jogador = "O" if jogador == "X" else "X"

        # Pergunta se quer jogar novamente
        resp = input("Jogar novamente? (s/n): ").strip().lower()
        if resp not in ("s", "sim", "y", "yes"):
            print("Obrigado por jogar!")
            break

if __name__ == "__main__":
    jogar()
