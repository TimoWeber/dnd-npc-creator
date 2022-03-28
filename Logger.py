from random import randint
from rich.console import Console
import configs.Switches as switches

console = Console()

def info(info_text: str, end="\n"):
    console.print("[cyan][ INFO ] [/ cyan] " + info_text,end=end, highlight=False)

def info_no_nl(info_text: str):
    console.print("[cyan][ INFO ] [/ cyan] " + info_text, end="", highlight=False)

def grey(info_text: str):
    console.print("[bold] [/ bold][white]" + info_text + "[/ white]", highlight=False)

def error(info_text: str):
    console.print("[red][ ERROR ][/ red] " + info_text)

def verbose(info_text: str):
    if switches.verbose:
        console.print("[yellow][ VERBOSE ][/ yellow] " + info_text)