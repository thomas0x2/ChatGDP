from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

def analyze_sentiment(news_list: list, model_name: str = "llama3.1") -> tuple[int, str]:
    """
    Analyzes the sentiment of the latest 5 news headlines using a local LLM.
    Returns a score (1-10) and a 1-sentence summary.
    """
    if not news_list:
        return 5, "No news found to analyze."
        
    headlines = [n.get('title', '') for n in news_list[:5]]
    context = "\n".join([f"- {h}" for h in headlines])
    
    prompt_template = ChatPromptTemplate.from_template("""
        You are a financial analyst. Analyze the sentiment of the following news headlines for a stock:
        
        {context}
        
        Output EXACTLY like this:
        Score: [1-10]
        Summary: [One sentence summary]
        
        Score 1 is extremely negative, 10 is extremely positive.
    """)
    
    try:
        model = OllamaLLM(model=model_name) 
        chain = prompt_template | model
        response = chain.invoke({"context": context})
        
        lines = response.split('\n')
        score = 5
        summary = "Could not parse analysis."
        
        for line in lines:
            if "Score:" in line:
                try:
                    score_str = line.split("Score:")[1].strip()
                    score = int(float(score_str.split('/')[0]))
                except Exception:
                    pass
            if "Summary:" in line:
                summary = line.split("Summary:")[1].strip()
                
        return score, summary
        
    except Exception as e:
        return 5, f"AI Analysis failed (Ensure Ollama is running): {str(e)}"
