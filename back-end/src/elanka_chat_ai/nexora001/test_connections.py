"""
Test connections to MongoDB and Google Gemini API. 
Run this to verify your configuration is working.
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent. parent
sys.path.insert(0, str(src_path))

from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

# Load . env from project root
project_root = Path(__file__).parent. parent. parent
load_dotenv(project_root / ".env")

console = Console()


def test_mongodb_connection():
    """Test MongoDB Atlas connection."""
    console.print("\n[cyan]Testing MongoDB Connection.. .[/cyan]")
    
    try:
        from pymongo import MongoClient
        
        mongodb_uri = os. getenv("MONGODB_URI", "")
        mongodb_database = os.getenv("MONGODB_DATABASE", "nexora001")
        
        if not mongodb_uri or "mongodb" not in mongodb_uri. lower():
            console.print("[red]❌ MONGODB_URI is not set in .env[/red]")
            console.print(f"   Current value: '{mongodb_uri[:50]}...' " if mongodb_uri else "   Current value: (empty)")
            return False
        
        # Connect with a short timeout
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection by listing databases
        databases = client.list_database_names()
        console.print(f"[green]✅ MongoDB Connected![/green]")
        console.print(f"   Available databases: {databases}")
        
        # Check if our database exists
        db = client[mongodb_database]
        collections = db.list_collection_names()
        console.print(f"   Database '{mongodb_database}' collections: {collections}")
        
        # Create documents collection if it doesn't exist
        if 'documents' not in collections:
            db.create_collection('documents')
            console.print(f"   [yellow]Created 'documents' collection[/yellow]")
        
        client.close()
        return True
        
    except Exception as e:
        console.print(f"[red]❌ MongoDB Connection Failed![/red]")
        console.print(f"   Error: {e}")
        return False


def test_google_gemini_connection():
    """Test Google Gemini API connection."""
    console.print("\n[cyan]Testing Google Gemini API...[/cyan]")
    
    try:
        import google.generativeai as genai
        
        api_key = os. getenv("GOOGLE_API_KEY", "")
        
        if not api_key or api_key. startswith("your_") or len(api_key) < 10:
            console. print("[red]❌ GOOGLE_API_KEY is not set in . env[/red]")
            return False
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # List available models
        models = []
        for m in genai.list_models():
            if 'generateContent' in m. supported_generation_methods:
                models.append(m.name)
        
        console.print(f"[green]✅ Google Gemini API Connected![/green]")
        console.print(f"   Available models: {models[:5]}...")
        
        # Use a model that exists (gemini-2.0-flash or gemini-1.5-flash)
        model_to_use = None
        preferred_models = ['gemini-2. 0-flash', 'gemini-2. 5-flash', 'gemini-1.5-flash']
        
        for preferred in preferred_models:
            for available in models:
                if preferred in available:
                    model_to_use = available. replace('models/', '')
                    break
            if model_to_use:
                break
        
        if not model_to_use:
            model_to_use = models[0]. replace('models/', '') if models else 'gemini-pro'
        
        console.print(f"   Using model: {model_to_use}")
        
        # Test a simple generation
        model = genai.GenerativeModel(model_to_use)
        response = model.generate_content("Say 'Hello Nexora001!' in exactly 3 words.")
        console.print(f"   Test response: {response.text. strip()}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Google Gemini API Failed![/red]")
        console.print(f"   Error: {e}")
        return False


def test_embedding_generation():
    """Test embedding generation for RAG."""
    console.print("\n[cyan]Testing Embedding Generation...[/cyan]")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY", "")
        
        if not api_key or len(api_key) < 10:
            console.print("[red]❌ GOOGLE_API_KEY is not set[/red]")
            return False
        
        genai.configure(api_key=api_key)
        
        # List embedding models
        embedding_models = []
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                embedding_models.append(m. name)
        
        console.print(f"   Available embedding models: {embedding_models[:3]}")
        
        # Use the first available embedding model
        embed_model = embedding_models[0] if embedding_models else "models/embedding-001"
        
        # Test embedding
        result = genai.embed_content(
            model=embed_model,
            content="This is a test sentence for Nexora001.",
            task_type="retrieval_document"
        )
        
        embedding = result['embedding']
        console.print(f"[green]✅ Embedding Generation Works![/green]")
        console.print(f"   Model used: {embed_model}")
        console. print(f"   Embedding dimensions: {len(embedding)}")
        console.print(f"   First 5 values: {[round(v, 4) for v in embedding[:5]]}")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        if "429" in error_str and "quota" in error_str.lower():
            console.print(f"[yellow]⚠️  Embedding API quota exceeded (Free tier limit)[/yellow]")
            console.print(f"   [dim]Note: Google free tier doesn't support embeddings[/dim]")
            console.print(f"   [dim]Consider: sentence-transformers or OpenAI embeddings[/dim]")
        else:
            console.print(f"[red]❌ Embedding Generation Failed![/red]")
            console.print(f"   Error: {e}")
        return False


def main():
    """Run all connection tests."""
    console.print(Panel(
        "[bold blue]Nexora001 Connection Tests[/bold blue]\n"
        "Testing MongoDB and Google Gemini API connections...",
        title="🔌 Connection Test"
    ))
    
    # Show what we're loading
    console.print("\n[dim]Loading from .env file...[/dim]")
    console.print(f"[dim]MONGODB_URI: {'Set ✓' if os. getenv('MONGODB_URI') else 'Not set ✗'}[/dim]")
    console.print(f"[dim]GOOGLE_API_KEY: {'Set ✓' if os.getenv('GOOGLE_API_KEY') else 'Not set ✗'}[/dim]")
    
    results = {
        "MongoDB": test_mongodb_connection(),
        "Google Gemini": test_google_gemini_connection(),
        "Embeddings": test_embedding_generation(),
    }
    
    # Summary
    console.print("\n" + "=" * 50)
    console. print("[bold]Summary:[/bold]")
    
    critical_passed = results["MongoDB"] and results["Google Gemini"]
    all_passed = all(results.values())
    
    for service, passed in results. items():
        status = "[green]✅ PASS[/green]" if passed else "[red]❌ FAIL[/red]"
        optional = " (optional)" if service == "Embeddings" else ""
        console.print(f"  {service}{optional}: {status}")
    
    console.print("=" * 50)
    
    if all_passed:
        console.print("\n[bold green]🎉 All connections successful!  Ready for Step 3![/bold green]\n")
    elif critical_passed:
        console.print("\n[bold cyan]✅ Critical connections working![/bold cyan]")
        console.print("[dim]Note: Embeddings are optional. You can use alternative embedding solutions.[/dim]\n")
    else:
        console. print("\n[bold yellow]⚠️ Some critical connections failed. Check your .env file.[/bold yellow]")
        console.print("[dim]Make sure there are no spaces in values and credentials are valid.[/dim]\n")
    
    return all_passed


if __name__ == "__main__":
    main()