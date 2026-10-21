import httpx
import warnings
import webbrowser
import urllib.parse
import re

def open_in_browser(url: str) -> str:
    """Opens a URL visually in the user's default desktop web browser."""
    try:
        webbrowser.open(url)
        return f"Successfully opened {url} in the user's visual web browser."
    except Exception as e:
        return f"Error opening browser: {str(e)}"

def play_youtube_video(search_query: str) -> str:
    """Searches for a YouTube video and directly plays the first result."""
    try:
        import urllib.request
        import urllib.parse
        import re
        import webbrowser
        
        encoded_query = urllib.parse.quote(search_query)
        html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={encoded_query}")
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        
        if video_ids:
            # We found the first video link
            video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            webbrowser.open(video_url)
            return f"Successfully opened and playing YouTube video for '{search_query}'. URL: {video_url}"
        else:
            # Fallback to search results if parsing fails
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(url)
            return f"Could not extract direct video link. Opened search results for '{search_query}'."
    except Exception as e:
        return f"Error playing YouTube video: {str(e)}"

def search_web(query: str, max_results: int = 3) -> str:
    """Search the web using Google Search via SerpApi."""
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("SERPAPI")
        if not api_key:
            return "Error: SERPAPI key not found in .env file."
            
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google"
        }
        
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
        # 1. Check for a direct answer box (great for weather, time, instant facts)
        answer_box = data.get("answer_box", {})
        if answer_box:
            ans = answer_box.get("answer") or answer_box.get("snippet") or str(answer_box)
            return f"Google Answer Box:\n{ans}"
            
        # 2. Parse standard organic results
        results = data.get("organic_results", [])
        if not results:
            return "No results found."
            
        formatted = []
        for i, r in enumerate(results[:max_results]):
            title = r.get("title", "Unknown Title")
            link = r.get("link", "")
            snippet = r.get("snippet", "")
            formatted.append(f"Result {i+1}:\nTitle: {title}\nURL: {link}\nSnippet: {snippet}")
            
        return "\n\n".join(formatted)
        
    except Exception as e:
        return f"Error searching web via SerpApi: {str(e)}"

def open_url(url: str) -> str:
    """Fetch the text content of a URL."""
    try:
        # Simple fetch and truncate to avoid blowing up context
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            text = response.text
            # Very naive html strip just for phase 2 proof of concept
            import re
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:2000] + ("..." if len(text) > 2000 else "")
    except Exception as e:
        return f"Error opening URL: {str(e)}"
