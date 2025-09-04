import os
import dotenv
from openai import OpenAI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import json

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def save_conversation_to_log(conversation, log_file):
    """Guarda la conversación en un archivo de log"""
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"=== LOG DE CONVERSACIÓN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        for idx, msg in enumerate(conversation, start=1):
            role = msg.get("role", "?").upper()
            content = msg.get("content", "")
            f.write(f"{idx:02d}. [{role}]: {content}\n")
        f.write(f"\n=== FIN DEL LOG ===\n")

def save_conversation_to_json(conversation, json_file):
    """Guarda la conversación en un archivo JSON"""
    conversation_data = {
        "timestamp": datetime.now().isoformat(),
        "conversation": conversation,
        "total_messages": len(conversation)
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(conversation_data, f, ensure_ascii=False, indent=2)

def load_conversation_from_json(json_file):
    """Carga una conversación desde un archivo JSON"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("conversation", [])
    except Exception as e:
        print(f"Error cargando conversación: {e}")
        return []

def get_available_conversations():
    """Obtiene la lista de conversaciones disponibles en la carpeta logs"""
    conversations = []
    if not os.path.exists("logs"):
        return conversations
    
    for filename in os.listdir("logs"):
        if filename.startswith("conversation_") and filename.endswith(".json"):
            filepath = os.path.join("logs", filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                conversations.append({
                    "filename": filename,
                    "filepath": filepath,
                    "timestamp": data.get("timestamp", ""),
                    "total_messages": data.get("total_messages", 0)
                })
            except:
                continue
    
    # Ordenar por timestamp (más reciente primero)
    conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    return conversations

def show_conversation_menu(console):
    """Muestra el menú de opciones y retorna la opción seleccionada"""
    console.print("\n[bold cyan]=== MENÚ DE OPCIONES ===[/bold cyan]")
    console.print("1. [green]Nuevo chat[/green]")
    console.print("2. [blue]Continuar chat anterior[/blue]")
    
    while True:
        try:
            choice = input("\nSelecciona una opción (1 o 2): ").strip()
            if choice in ["1", "2"]:
                return choice
            else:
                console.print("[red]Opción inválida. Por favor, selecciona 1 o 2.[/red]")
        except KeyboardInterrupt:
            console.print("\n[red]Saliendo...[/red]")
            return "1"

def show_conversation_list(console, conversations):
    """Muestra la lista de conversaciones disponibles"""
    if not conversations:
        console.print("[yellow]No hay conversaciones anteriores disponibles.[/yellow]")
        return None
    
    console.print(f"\n[bold blue]Conversaciones disponibles ({len(conversations)}):[/bold blue]")
    for i, conv in enumerate(conversations, 1):
        timestamp = conv["timestamp"][:19].replace("T", " ") if conv["timestamp"] else "Desconocido"
        console.print(f"{i:2d}. [cyan]{conv['filename']}[/cyan] - {timestamp} ({conv['total_messages']} mensajes)")
    
    while True:
        try:
            choice = input(f"\nSelecciona una conversación (1-{len(conversations)}) o 0 para cancelar: ").strip()
            if choice == "0":
                return None
            choice_num = int(choice)
            if 1 <= choice_num <= len(conversations):
                return conversations[choice_num - 1]
            else:
                console.print(f"[red]Opción inválida. Por favor, selecciona 1-{len(conversations)} o 0.[/red]")
        except ValueError:
            console.print("[red]Por favor, introduce un número válido.[/red]")
        except KeyboardInterrupt:
            console.print("\n[red]Cancelando...[/red]")
            return None

def main():
    console = Console()
    console.print("Stateful Chatbot (Completions API, type 'exit' to quit)", style="bold cyan")
    
    # Mostrar menú de opciones
    choice = show_conversation_menu(console)
    
    model = "gpt-4o-mini"
    conversation = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    
    if choice == "2":
        # Cargar conversación anterior
        conversations = get_available_conversations()
        selected_conv = show_conversation_list(console, conversations)
        
        if selected_conv:
            loaded_conversation = load_conversation_from_json(selected_conv["filepath"])
            # Mantener el mensaje del sistema y añadir la conversación cargada
            conversation = [{"role": "system", "content": "You are a helpful assistant."}] + loaded_conversation
            console.print(f"[green]Conversación cargada: {selected_conv['filename']}[/green]")
            console.print(f"[dim]Mensajes cargados: {len(loaded_conversation)}[/dim]")
            
            # Usar el archivo existente para continuar guardando
            log_path = selected_conv["filepath"].replace("conversation_", "log_").replace(".json", ".txt")
            json_path = selected_conv["filepath"]
        else:
            console.print("[yellow]Iniciando nuevo chat...[/yellow]")
            choice = "1"
    
    if choice == "1":
        # Nuevo chat
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        log_filename = f"log_{timestamp}.txt"
        json_filename = f"conversation_{timestamp}.json"
        log_path = os.path.join("logs", log_filename)
        json_path = os.path.join("logs", json_filename)
        console.print(f"[dim]Conversación se guardará en: {log_path}[/dim]")
        console.print(f"[dim]JSON se guardará en: {json_path}[/dim]")
    while True:
        console.print("You: ", style="bold green", end="")
        user_input = input()
        if user_input.lower() in {"exit", "quit"}:
            # Guardar conversación antes de salir
            save_conversation_to_log(conversation, log_path)
            save_conversation_to_json(conversation, json_path)
            console.print(f"[green]Conversación guardada en: {log_path}[/green]")
            console.print(f"[green]JSON guardado en: {json_path}[/green]")
            console.print("Goodbye!")
            break
        # Mostrar contexto si el usuario lo solicita
        if user_input.strip().lower() == "contexto":
            if not conversation:
                console.print(Panel.fit("(vacío)", title="Contexto de la conversación", border_style="yellow"))
            else:
                table = Table(title="Contexto de la conversación", show_lines=True, header_style="bold blue")
                table.add_column("#", style="dim", width=4)
                table.add_column("Rol", style="magenta", width=10)
                table.add_column("Contenido", style="white")
                for idx, msg in enumerate(conversation, start=1):
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    table.add_row(f"{idx:02d}", role, content)
                console.print(table)
            continue
        conversation.append({"role": "user", "content": user_input})
        try:
            response = client.chat.completions.create(
                model=model,
                messages=conversation
            )
            text = response.choices[0].message.content.strip()
            console.print(Panel.fit(text, title="Bot", title_align="left", border_style="cyan"))
            conversation.append({"role": "assistant", "content": text})
            
            # Guardar conversación automáticamente después de cada intercambio
            save_conversation_to_log(conversation, log_path)
            save_conversation_to_json(conversation, json_path)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
