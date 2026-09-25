# %% [markdown]
# # UI Module
# Implements a colorful CLI console interface using colorama and tqdm.

# %%
import os
import platform
import sys
from typing import Dict, Any, List
from colorama import init, Fore, Back, Style
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

# %%
class UI:
    """Provides formatting and drawing utilities for the Command Line Interface."""

    @staticmethod
    def clear() -> None:
        """Clears the console screen."""
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")

    @staticmethod
    def header() -> None:
        """Renders the stylized application banner."""
        print(f"{Fore.MAGENTA}{Style.BRIGHT}" + "=" * 50)
        print(f"{Fore.CYAN}{Style.BRIGHT}  ⚡ STEAMTOOLS AUTO GAME ADDER v2.0 ⚡")
        print(f"{Fore.BLUE}{Style.DIM}     Bring Games Directly to Your Library")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}" + "=" * 50)
        print()

    @staticmethod
    def menu(current_path: str) -> None:
        """Draws the main interactive menu with configurations details."""
        UI.header()
        
        # Display current configuration status
        status_color = Fore.GREEN if current_path else Fore.RED
        path_display = current_path if current_path else "Not set! Please configure."
        
        print(f"{Fore.YELLOW}Current Steam Path:{Style.RESET_ALL} {status_color}{path_display}")
        print("-" * 50)
        print(f"[{Fore.GREEN}1{Fore.RESET}] Add Game (Enter AppID)")
        print(f"[{Fore.GREEN}2{Fore.RESET}] Remove Game / Rollback AppID")
        print(f"[{Fore.GREEN}3{Fore.RESET}] Change / Set Steam Path")
        print(f"[{Fore.GREEN}4{Fore.RESET}] View App Logs")
        print(f"[{Fore.GREEN}5{Fore.RESET}] Exit")
        print("-" * 50)
        print(f"{Fore.CYAN}Select an option [1-5]: ", end="")

    @staticmethod
    def error(message: str) -> None:
        """Prints a red error message."""
        print(f"\n{Fore.RED}{Style.BRIGHT}❌ ERROR: {message}\n")

    @staticmethod
    def success(message: str) -> None:
        """Prints a green success message."""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ SUCCESS: {message}\n")

    @staticmethod
    def info(message: str) -> None:
        """Prints a cyan informational message."""
        print(f"{Fore.CYAN}[*] {message}")

    @staticmethod
    def warn(message: str) -> None:
        """Prints a yellow warning message."""
        print(f"{Fore.YELLOW}[!] WARNING: {message}")

    @staticmethod
    def show_game_card(details: Dict[str, Any]) -> None:
        """Displays rich information about the retrieved game in a styled panel."""
        print()
        print(f"{Fore.YELLOW}{Style.BRIGHT}┌──────────────────────────────────────────────┐")
        print(f"{Fore.YELLOW}{Style.BRIGHT}│               GAME METADATA                  │")
        print(f"{Fore.YELLOW}{Style.BRIGHT}└──────────────────────────────────────────────┘")
        
        name = details.get("name", "Unknown Game")[:38]
        g_type = details.get("type", "game").upper()
        metacritic = details.get("metacritic_score", "N/A")
        age = details.get("required_age", 0)
        is_free = "Yes" if details.get("is_free") else "No"
        
        print(f" {Fore.CYAN}{Style.BRIGHT}Name:{Fore.RESET}        {name}")
        print(f" {Fore.CYAN}{Style.BRIGHT}Type:{Fore.RESET}        {g_type}")
        print(f" {Fore.CYAN}{Style.BRIGHT}Metacritic:{Fore.RESET}  {Fore.GREEN if metacritic != 'N/A' else Fore.RESET}{metacritic}")
        print(f" {Fore.CYAN}{Style.BRIGHT}Age Rating:{Fore.RESET}  {Fore.RED if age else Fore.RESET}{age}+")
        print(f" {Fore.CYAN}{Style.BRIGHT}Free-to-Play:{Fore.RESET}{is_free}")
        
        desc = details.get("short_description", "")
        if desc:
            # Clean HTML tags and wrap text slightly
            clean_desc = desc.replace("&quot;", '"').replace("<br>", "").replace("<br/>", "")
            clean_desc = clean_desc[:120] + "..." if len(clean_desc) > 120 else clean_desc
            print(f" {Fore.CYAN}{Style.BRIGHT}Description:{Fore.RESET} {clean_desc}")
            
        print(f"{Fore.YELLOW}" + "─" * 48)
        print()

    @staticmethod
    def select_library_menu(libraries: List[Tuple[str, str]]) -> str:
        """Asks user to select which library to add the game to."""
        print()
        print(f"{Fore.YELLOW}Multiple Steam libraries detected:")
        for idx, path in libraries:
            print(f"  [{Fore.GREEN}{idx}{Fore.RESET}] {path}")
        print(f"{Fore.YELLOW}Select target library index (Default 0): ", end="")
        choice = input().strip()
        
        # Validate selection
        valid_indices = [idx for idx, _ in libraries]
        if choice in valid_indices:
            return choice
        return "0"

    @staticmethod
    def show_logs(log_path: str, lines_count: int = 40) -> None:
        """Displays the tail of the application logs."""
        UI.clear()
        UI.header()
        print(f"{Fore.CYAN}Showing last {lines_count} lines of logs from: {log_path}\n" + "-" * 50)
        
        if not os.path.exists(log_path):
            print(f"{Fore.RED}No log file found yet.")
            print("-" * 50)
            return
            
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                tail = lines[-lines_count:]
                for line in tail:
                    print(line, end="")
        except Exception as e:
            print(f"{Fore.RED}Failed to read logs: {e}")
            
        print("\n" + "-" * 50)
        input(f"\nPress {Fore.GREEN}Enter{Fore.RESET} to return to main menu...")

    @staticmethod
    def get_progress_bar(total: int, desc: str) -> tqdm:
        """Returns a configured tqdm progress bar instance."""
        return tqdm(
            total=total,
            desc=desc,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}]"
        )
