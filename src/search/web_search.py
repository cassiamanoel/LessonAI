from duckduckgo_search import DDGS
import json

def search_web(query: str, max_results: int = 5) -> str:
    """Realiza uma busca no DuckDuckGo e retorna os resultados formatados."""
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            formatted_results = []
            for r in results:
                formatted_results.append(f"Título: {r['title']}\nLink: {r['href']}\nResumo: {r['body']}\n")
            return "\n".join(formatted_results)
    except Exception as e:
        return f"Erro na busca: {str(e)}"

if __name__ == "__main__":
    # Teste rápido
    print(search_web("Inteligência Artificial explicada para crianças"))
