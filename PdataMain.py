import json
import os
import sys
from colorama import init, Fore, Style

init(autoreset=True)


class PDataConnection:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {}
        self._connect()

    def _connect(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {}
        else:
            self.data = {}

    def upsert(self, key, value):
        self.data[key] = value

    def select(self, key):
        return self.data.get(key, None)

    def select_all(self):
        return self.data.copy()

    def delete(self, key):
        if key in self.data:
            del self.data[key]
            return True
        return False

    def commit(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def close(self):
        self.commit()
        self.data.clear()


def connect(filepath="pdata.db.json"):
    return PDataConnection(filepath)


def print_header():
    print(f"{Fore.CYAN}PData CLI (SQLite-like Key-Value Store){Style.RESET_ALL}")
    print(f"Enter '.help' for usage hints.\n")


def print_help():
    print(f"\n{Fore.YELLOW}Commands:{Style.RESET_ALL}")
    print("  SET <key> <value>   - Insert or update a record")
    print("  GET <key>           - Retrieve a record by key")
    print("  DEL <key>           - Delete a record")
    print("  SELECT *            - Show all records")
    print("  COMMIT              - Save changes to disk")
    print("  .exit               - Save and exit shell")
    print("  .help               - Show this message\n")


def run_shell(db_file="storage.db.json"):
    db = connect(db_file)
    print_header()

    while True:
        try:
            cmd_input = input(f"{Fore.BLUE}pdata> {Style.RESET_ALL}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not cmd_input:
            continue

        parts = cmd_input.split(maxsplit=2)
        command = parts[0].upper()

        if command in (".EXIT", "EXIT", "QUIT"):
            db.close()
            print(f"{Fore.MAGENTA}Changes committed. Disconnected from PData.{Style.RESET_ALL}")
            break

        elif command == ".HELP":
            print_help()

        elif command == "COMMIT":
            db.commit()
            print(f"{Fore.GREEN}✓ Changes saved to '{db.filepath}'.{Style.RESET_ALL}")

        elif command == "SET" and len(parts) >= 3:
            key, value = parts[1], parts[2]
            db.upsert(key, value)
            print(f"{Fore.GREEN}✓ Row inserted/updated: [{key}]{Style.RESET_ALL}")

        elif command == "GET" and len(parts) >= 2:
            key = parts[1]
            val = db.select(key)
            if val is not None:
                print(f"{Fore.GREEN}{key}{Style.RESET_ALL} : {Fore.YELLOW}{val}{Style.RESET_ALL}")
            else:
                print(f"{Fore.LIGHTBLACK_EX}Empty set (key not found).{Style.RESET_ALL}")

        elif command == "DEL" and len(parts) >= 2:
            key = parts[1]
            if db.delete(key):
                print(f"{Fore.RED}✓ Row deleted: [{key}]{Style.RESET_ALL}")
            else:
                print(f"{Fore.LIGHTBLACK_EX}Key '{key}' does not exist.{Style.RESET_ALL}")

        elif command == "SELECT" and len(parts) >= 2 and parts[1] == "*":
            records = db.select_all()
            if not records:
                print(f"{Fore.LIGHTBLACK_EX}Database is empty.{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.CYAN}--- Records ---{Style.RESET_ALL}")
                for k, v in records.items():
                    print(f" {Fore.GREEN}{k}{Style.RESET_ALL} | {Fore.YELLOW}{v}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}---------------{Style.RESET_ALL} ({len(records)} rows)\n")

        else:
            print(f"{Fore.RED}Error near '{parts[0]}': syntax error (type .help for commands){Style.RESET_ALL}")


if __name__ == "__main__":
    run_shell()
