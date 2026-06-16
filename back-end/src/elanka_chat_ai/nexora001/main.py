"""
Nexora002 - Multi-Tenant Console (Admin + Client + User Modes)
This is the interactive console interface for the Nexora002 system.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import hashlib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexora001.config import settings, print_config_status
from nexora001.storage.mongodb import get_storage
from nexora001.crawler.manager import crawl_website
from nexora001.rag.pipeline import create_rag_pipeline
from nexora001.processors.pdf_processor import PDFProcessor
from nexora001.processors.docx_processor import DOCXProcessor

console = Console()

# --- SESSION STATE ---
# This simulates the "Logged In" user
CURRENT_USER = None
# Global RAG pipeline (initialized on first use)
_rag_pipeline = None

def print_banner():
    """Display the application banner."""
    banner = """
    ███╗   ██╗███████╗██╗  ██╗ ██████╗ ██████╗  █████╗     ██████╗  ██████╗ ██╗
    ████╗  ██║██╔════╝╚██╗██╔╝██╔═══██╗██╔══██╗██╔══██╗   ██╔═████╗██╔═████╗███║
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║██████╔╝███████║   ██║██╔██║██║██╔██║╚██║
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║██╔══██╗██╔══██║   ████╔╝██║████╔╝██║ ██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝██║  ██║██║  ██║   ╚██████╔╝╚██████╔╝ ██║
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝  ╚═════╝  ╚═╝
                                                                             
           AI-Powered Knowledge Base Chatbot with RAG -- Multi-Tenant SaaS Edition
    """
    console.print(Panel(banner, style="bold Purple"))


def get_rag_pipeline():
    """Get or create RAG pipeline."""
    global _rag_pipeline
    if _rag_pipeline is None:
        console.print("[dim]Initializing AI Engine...[/dim]")
        try:
            # Note: We don't pass client_id here anymore, we pass it during 'ask'
            _rag_pipeline = create_rag_pipeline(
                embedding_provider="sentence_transformers",
                model_name="gemini-2.5-flash"
            )
        except Exception as e:
            console.print(f"[red]AI Init Failed: {e}[/red]")
            return None
    return _rag_pipeline

# ==========================================
# AUTH & SESSION
# ==========================================

def handle_register():
    console.print("\n[cyan]📝 Create New Client Account[/cyan]")
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True)
    name = Prompt.ask("Company/Name")
    
    # Simple hash for demo (Use bcrypt in production!)
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        with get_storage() as storage:
            user_id = storage.create_user(email, pass_hash, name=name)
            console.print(f"[green]✅ Account created! ID: {user_id}[/green]")
            console.print("Please login now.")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def handle_login():
    global CURRENT_USER
    console.print("\n[cyan]🔐 Login[/cyan]")
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True)
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    
    with get_storage() as storage:
        # Find user
        user = storage.users.find_one({"email": email, "password_hash": pass_hash})
        
        if user:
            if user.get('status') == 'banned':
                console.print("[bold red]⛔ This account has been suspended by the Administrator.[/bold red]\n")
                return
            
            CURRENT_USER = user
            CURRENT_USER["_id"] = str(user["_id"])
            role = user.get('role', 'client_admin')
            color = "red" if role == "super_admin" else "green"
            console.print(f"\n[bold {color}]👋 Welcome back, {user.get('name')} ({role}))![/bold {color}]")
        else:
            console.print("[red]❌ Invalid credentials[/red]\n")

def handle_logout():
    global CURRENT_USER
    if Confirm.ask("Are you sure you want to logout?"):
        CURRENT_USER = None
        console.print("[yellow]👋 Logged out successfully.[/yellow]")

def handle_whoami():
    if CURRENT_USER:
        console.print(Panel(
            f"User: {CURRENT_USER['name']}\nEmail: {CURRENT_USER['email']}\nRole: {CURRENT_USER['role']}\nID: {CURRENT_USER['_id']}",
            title="👤 Current Session",
            border_style="green"
        ))
    else:
        console.print("[yellow]🕵️  You are currently: GUEST (Not logged in)[/yellow]")

# ==========================================
# CLIENT ADMIN COMMANDS (UPDATED)
# ==========================================

def handle_list():
    if not CURRENT_USER:
        console.print("[red]⛔ Access Denied: Please 'login' first.[/red]")
        return True

    console.print(f"\n[cyan]📄 Documents for {CURRENT_USER['name']}[/cyan]")
    console.print("─" * 80)
    
    try:
        with get_storage() as storage:
            # Fetch ONLY this client's documents
            # Note: We use .find() directly here for simplicity
            cursor = storage.documents.find(
                {"client_id": CURRENT_USER['_id']},
                {"metadata": 1, "content": 1}
            ).limit(20)
            
            documents = list(cursor)
            
            if not documents:
                console.print("[yellow]No documents found. Use 'crawl' to add content.[/yellow]\n")
                return True
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Doc ID", style="dim", width=24)
            table.add_column("Title", style="cyan", width=40)
            table.add_column("URL", style="blue", width=50)
            table.add_column("Size", justify="right", width=10)
            
            for i, doc in enumerate(documents, 1):
                meta = doc.get('metadata', {})
                content_len = len(doc.get('content', ''))
                
                table.add_row(
                    str(doc["_id"]),
                    meta.get('title', 'Untitled')[:38],
                    meta.get('source_url', 'Unknown')[:48],
                    f"{content_len:,} ch"
                )
            
            console.print(table)
            console.print(f"\n[dim]Showing {len(documents)} documents[/dim]\n")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]\n")
    return True

def handle_crawl(args: str):
    if not CURRENT_USER:
        console.print("[red]⛔ Access Denied: Please 'login' first.[/red]")
        return True

    if not args:
        console.print("[red]Usage: crawl <url> [--depth N] [--playwright][/red]")
        return True

    # Parse arguments
    parts = args.split()
    url = parts[0]
    
    # Parse --depth flag
    max_depth = 2  # Default
    if '--depth' in parts:
        try:
            depth_idx = parts.index('--depth')
            if depth_idx + 1 < len(parts):
                max_depth = int(parts[depth_idx + 1])
        except (ValueError, IndexError):
            console.print("[yellow]⚠️  Invalid depth, using default: 2[/yellow]")
    
    # Parse --playwright flag
    use_playwright = '--playwright' in parts
    
    # PASS CLIENT_ID TO CRAWLER
    try:
        mode = "Playwright (JS)" if use_playwright else "Standard"
        console.print(f"\n[cyan]🕷️  Crawling for client: {CURRENT_USER['name']} (depth: {max_depth}, mode: {mode})...[/cyan]")
        crawl_website(
            url=url,
            client_id=CURRENT_USER['_id'],
            max_depth=max_depth,
            follow_links=True,
            use_playwright=use_playwright
        )
        console.print("[green]✅ Crawl complete and data isolated.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    return True

def handle_upload(args: str):
    """Handle document upload (PDF/DOCX)."""
    if not CURRENT_USER:
        console.print("[red]Please login first.[/red]")
        return True

    if not args:
        console.print("[yellow]Usage: upload <file_path>[/yellow]")
        return True

    file_path = args.strip()
    
    # Check if file exists
    if not Path(file_path).exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return True
    
    # Get file extension
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext not in ['.pdf', '.docx']:
        console.print(f"[red]Unsupported file type: {file_ext}[/red]")
        console.print("[yellow]Supported formats: .pdf, .docx[/yellow]")
        return True
    
    console.print(f"\n[cyan]📄 Processing {Path(file_path).name}...[/cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Uploading and processing document...", total=None)
            
            # Process based on file type
            if file_ext == '.pdf':
                processor = PDFProcessor(generate_embeddings=True)
                result = processor.process_and_store(
                    pdf_path=file_path,
                    client_id=str(CURRENT_USER['_id']),
                    source_url=f"file://{Path(file_path).absolute()}"
                )
            else:  # .docx
                processor = DOCXProcessor(generate_embeddings=True)
                result = processor.process_and_store(
                    docx_path=file_path,
                    client_id=str(CURRENT_USER['_id']),
                    source_url=f"file://{Path(file_path).absolute()}"
                )
            
            progress.update(task, completed=True)
        
        if result.get('success'):
            console.print(f"\n[green]✅ Document processed successfully![/green]")
            console.print(f"[cyan]File: {result.get('filename', 'Unknown')}[/cyan]")
            console.print(f"[cyan]Title: {result.get('title', 'Unknown')}[/cyan]")
            console.print(f"[cyan]Chunks created: {result.get('chunks_created', 0)}[/cyan]")
        else:
            console.print(f"\n[red]❌ Failed to process document[/red]")
            console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    return True

def handle_ask(args: str):
    if not CURRENT_USER:
        console.print("[red]⛔ Access Denied: Please 'login' first.[/red]")
        return True
    
    if not args:
        console.print("[red]Usage: ask <question>[/red]")
        return True

    rag = get_rag_pipeline()
    if not rag: return True

    console_session_id = f"session-session-{CURRENT_USER['_id']}"

    console.print(f"\n[cyan]🤔 Searching knowledge base for {CURRENT_USER['name']}...[/cyan]")
    
    try:
        # PASS CLIENT_ID TO RAG
        result = rag.ask(
            query=args, 
            client_id=CURRENT_USER['_id'],
            session_id=console_session_id,
            use_history=True
        )
        
        console.print(Panel(Markdown(result['answer']), title="🤖 Nexora AI"))
        
        if result.get('sources'):
            console.print("\n[dim]📚 Sources (Authenticated Access Only):[/dim]")
            for src in result['sources']:
                console.print(f" - {src['url']} ({src['score']:.0%})")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    return True

def handle_apikey():
    """Generate API Key for the current user."""
    if not CURRENT_USER:
        console.print("[red]⛔ Please login first.[/red]")
        return True

    if CURRENT_USER['role'] != 'client_admin':
        console.print("[red]⛔ Only Client Admins can generate keys.[/red]")
        return True

    try:
        with get_storage() as storage:
            key = storage.get_or_create_api_key(client_id=CURRENT_USER['_id'])
            console.print("\n[green]🔑 API Key Generated:[/green]")
            console.print(Panel(key, style="bold yellow"))
            console.print("[dim]Use this in your frontend widget integration.[/dim]\n")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    return True


def handle_delete_docs(args: str):
    if not CURRENT_USER: return
    if not args:
        console.print("[red]Usage: delete <doc_id> OR delete <url>[/red]")
        return
    
    target = args.split()[0]
    
    # Check if input looks like a MongoDB ObjectId (24 hex characters)
    import re
    is_id = re.match(r'^[0-9a-fA-F]{24}$', target)
    
    with get_storage() as s:
        if is_id:
            # DELETE BY ID (Single Chunk)
            if Confirm.ask(f"Delete single document/chunk {target}?"):
                success = s.delete_document_by_id(CURRENT_USER['_id'], target)
                if success:
                    console.print(f"[green]✅ Document deleted successfully.[/green]")
                else:
                    console.print(f"[red]❌ Document not found.[/red]")
        else:
            # DELETE BY URL (All chunks from that site)
            if Confirm.ask(f"Delete ALL documents from URL {target}?"):
                count = s.delete_by_url(CURRENT_USER['_id'], target)
                if count > 0:
                    console.print(f"[green]✅ Deleted {count} documents.[/green]")
                else:
                    console.print(f"[yellow]No documents found for that URL.[/yellow]")


# ==========================================
#  SUPER ADMIN COMMANDS
# ==========================================

def require_admin():
    if not CURRENT_USER or CURRENT_USER.get('role') != 'super_admin':
        console.print("[red]⛔ Access Denied: Super Admin only.[/red]")
        return False
    return True

def handle_admin_users():
    """List all users and their stats."""
    if CURRENT_USER.get('role') != 'super_admin':
        console.print("[red]⛔ Permission Denied[/red]")
        return

    with get_storage() as storage:
        users = storage.get_all_users()
        
        table = Table(title="Nexora Clients", header_style="bold red")
        table.add_column("ID", style="dim", width=24)
        table.add_column("Name", style="white")
        table.add_column("Email", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Docs", justify="right")
        
        for u in users:
            status_style = "red" if u.get("status") == "banned" else "green"
            table.add_row(
                str(u["_id"]),
                u.get("name", "Unknown"),
                u["email"],
                u.get("role", "client"),
                f"[{status_style}]{u.get('status', 'active')}[/{status_style}]",
                str(u.get("doc_count", 0))
            )
        console.print(table)

def handle_admin_ban(args: str):
    """Ban a user by email."""
    if CURRENT_USER.get('role') != 'super_admin': return
    email = args.strip()
    with get_storage() as s:
        if s.ban_user(email):
            console.print(f"[red]🚫 User {email} has been BANNED.[/red]")
        else:
            console.print("[yellow]User not found.[/yellow]")

def handle_admin_unban(args: str):
    if not require_admin(): return
    email = args.strip()
    with get_storage() as s:
        if s.set_user_status(email, "active"):
            console.print(f"[green]✅ User {email} has been UNBANNED.[/green]")
        else:
            console.print("[yellow]User not found.[/yellow]")

def handle_admin_delete_client(args: str):
    if not require_admin(): return
    email = args.strip()
    
    console.print(f"[bold red]⚠️ WARNING: You are about to delete client {email}[/bold red]")
    console.print("This will remove their Account, Documents, API Keys, and Chat History.")
    
    if Confirm.ask("Are you ABSOLUTELY sure?", default=False):
        with get_storage() as s:
            count = s.delete_user_full(email)
            if count > 0:
                console.print(f"[green]✅ Deleted user and {count} associated records.[/green]")
            else:
                console.print("[yellow]User not found.[/yellow]")

# ==========================================
#  END USER WIDGET SIMULATION
# ==========================================

def handle_simulate_widget():
    """Simulates what happens on the Client's website."""
    console.print(Panel("🌐 Widget Simulator\nTest your chatbot as an anonymous visitor.", style="blue"))
    
    api_key = Prompt.ask("Enter the API Key (generated by Client Admin)")
    
    with get_storage() as storage:
        client_id = storage.validate_api_key(api_key)
        
        if not client_id:
            console.print("[red]❌ Invalid or inactive API Key.[/red]")
            return

        console.print(f"[green]✅ Connected to Knowledge Base ID: {client_id}[/green]")
        console.print("[dim]Type 'exit' to close the chat widget.[/dim]\n")
        
        # Initialize RAG
        from nexora001.rag.pipeline import create_rag_pipeline
        rag = create_rag_pipeline(model_name="gemini-2.5-flash")
        
        # Generate a temporary session ID for this visitor
        import uuid
        session_id = f"visitor-{uuid.uuid4().hex[:8]}"
        
        while True:
            q = Prompt.ask(f"[blue]Visitor[/blue]")
            if q.lower() in ['exit', 'quit']: break
            
            with console.status("Thinking..."):
                result = rag.ask(q, client_id=client_id, session_id=session_id)
            
            console.print(f"[green]Bot:[/green] {result['answer']}")
            if result['sources']:
                console.print(f"[dim]Sources: {len(result['sources'])} found[/dim]\n")

# ==========================================
# CLIENT ADMIN COMMANDS
# ==========================================

def handle_profile():
    """View and edit profile."""
    if not CURRENT_USER: return
    console.print(Panel(
        f"Name: {CURRENT_USER.get('name')}\nEmail: {CURRENT_USER['email']}\nRole: {CURRENT_USER.get('role')}",
        title="👤 Your Profile"
    ))
    
    if Confirm.ask("Do you want to edit your profile?"):
        new_name = Prompt.ask("New Name", default=CURRENT_USER.get('name'))
        new_email = Prompt.ask("New Email", default=CURRENT_USER['email'])
        
        with get_storage() as s:
            s.update_user_profile(CURRENT_USER['_id'], {"name": new_name, "email": new_email})
            console.print("[green]✅ Profile updated! Please re-login to see changes.[/green]")

# ==========================================
# MAIN LOOP
# ==========================================

def print_help():
    help_text = """
## Authentication
| Command | Description |
|---------|-------------|
| `register` | Create a new Client Admin account |
| `login` | Log in to an account |
| `logout` | Log out of the current account |
| `whoami` | Show current user |
| `apikey` | Generate widget key (Client Admin only) |

## Knowledge Base
| Command | Description |
|---------|-------------|
| `crawl <url>` | Crawl website (Saved to YOUR account) |
| `upload <file>` | Upload PDF or DOCX document |
| `ask <msg>` | Ask question (Searches YOUR data only) |
| `list` | List your documents |
| `widget` | Simulate end-user widget chat |
| `profile` | View and edit your profile |
| `delete <doc_id>` | Delete a document by ID |

## Admin Commands (Super Admin only)
| Command | Description |
|---------|-------------|
| `users` | List all users |
| `ban <email>` | Ban a user by email |
| `unban <email>` | Unban a user by email |
| `delete_client <email>` | Delete a client and all their data |
| `list` | List all documents (all clients) |
| `delete <doc_id>` | Delete a document by ID |
| `list_clients` | List all clients |
| `delete_client <client_id>` | Delete a client and all their data |

## General
| Command | Description |
|---------|-------------|
| `help` | Show this help |
| `clear` | Clear the console |
| `exit` | Quit |
    """
    console.print(Markdown(help_text))

def handle_command(command: str) -> bool:
    command = command.strip()
    if not command: return True
    
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "exit": return False
    elif cmd == "help": print_help()
    elif cmd == "clear": console.clear(); print_banner()
    
    # Auth Commands
    elif cmd == "register": handle_register()
    elif cmd == "login": handle_login()
    elif cmd == "logout": handle_logout()
    elif cmd == "whoami": handle_whoami()
    elif cmd == "apikey": handle_apikey()
    
    # Core Commands
    elif cmd == "crawl": handle_crawl(args)
    elif cmd == "upload": handle_upload(args)
    elif cmd == "ask": handle_ask(args)
    elif cmd == "list": handle_list()
    elif cmd == "widget": handle_simulate_widget()
    elif cmd == "users": handle_admin_users()
    elif cmd == "ban": handle_admin_ban(args)
    elif cmd == "profile": handle_profile()
    elif cmd == "delete": handle_delete_docs(args)
    elif cmd == "unban": handle_admin_unban(args)
    elif cmd == "delete_client": handle_admin_delete_client(args)
    
    # Add handlers for list/delete similarly...
    
    else:
        console.print(f"[red]Unknown command. Try 'help'.[/red]")
    
    return True

def main():
    print_banner()
    console.print("[yellow]⚠️  System Mode: Multi-Tenant SaaS Simulation[/yellow]")
    console.print("Please `register` or `login` to begin.\n")
    
    running = True
    while running:
        try:
            # Change prompt color based on login status
            prompt_str = f"[bold green]{CURRENT_USER['name']}[/bold green]" if CURRENT_USER else "[bold red]Guest[/bold red]"
            command = Prompt.ask(f"{prompt_str}@nexora")
            running = handle_command(command)
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]System Error: {e}[/red]")

if __name__ == "__main__":
    main()