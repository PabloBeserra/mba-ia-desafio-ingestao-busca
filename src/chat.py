from search import search_prompt

def main():
    # Inicializa o loop interativo no terminal.
    print("Chat iniciado. Digite sua pergunta ou 'sair' para encerrar.")

    while True:
        # Leitura da pergunta do usuario.
        question = input("\nPERGUNTA: ").strip()

        # Comandos para encerrar a sessao.
        if question.lower() in {"sair", "exit", "quit"}:
            print("Encerrando chat.")
            break

        # Evita chamadas de busca com entrada vazia.
        if not question:
            print("RESPOSTA: Informe uma pergunta valida.")
            continue

        try:
            # Executa busca semantica + resposta com LLM.
            answer = search_prompt(question)
            print(f"RESPOSTA: {answer}")
        except Exception as exc:
            # Mantem o chat ativo mesmo se ocorrer erro pontual.
            print(f"RESPOSTA: Erro ao processar pergunta: {exc}")

if __name__ == "__main__":
    main()