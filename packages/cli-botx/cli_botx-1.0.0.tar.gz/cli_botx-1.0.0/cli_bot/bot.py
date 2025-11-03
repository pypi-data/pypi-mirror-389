import datetime
import random
import webbrowser
import urllib.parse
import os
import ast
import operator as op

# ---------- Calculator (Safe Evaluation) ----------
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg
}

def safe_eval(expr):
    """Safely evaluate a math expression"""
    def _eval(node):
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):  # binary operations
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):  # -n
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise ValueError("Unsupported expression")

    return _eval(ast.parse(expr, mode='eval').body)

# ---------- Help Menu ----------
def show_help():
    print("Available Commands:")
    print("  hello              → Greet the bot")
    print("  time               → Show current time")
    print("  open <site>        → Open a site (Google, YouTube, GitHub, Reddit, Wikipedia, LinkedIn, Twitter, ChatGPT, Gemini, Perplexity)")
    print("  search <query>     → Search something on Google")
    print("  calc <expression>  → Solve a math expression (e.g. calc 2+3*4)")
    print("  help               → Show this help menu again")
    print("  exit               → Quit the bot")
    print("  --- To-Do List ---")
    print("  add <task>         → Add a new task")
    print("  list               → Show all tasks")
    print("  done <num>         → Mark a task as completed (use task number)")
    print("  clear              → Remove all tasks")
    print("-" * 40)

# ---------- Main Bot ----------
def main():
    print("Welcome to CLI Bot!")
    show_help()

    TASKS_FILE = "tasks.txt"

    # Load tasks if file exists
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            tasks = [line.strip() for line in f.readlines()]
    else:
        tasks = []

    while True:
        command = input("> ").strip()

        if command.lower() == "hello":
            print("Hello there! How can I help you?")

        elif command.lower() == "time":
            now = datetime.datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")
            print(f"Current time: {now}")

        elif command.lower().startswith("open "):
            site = command.split(" ", 1)[1].lower()
            sites = {
                "google": "https://www.google.com",
                "youtube": "https://www.youtube.com",
                "github": "https://github.com",
                "reddit": "https://www.reddit.com",
                "wikipedia": "https://www.wikipedia.org",
                "linkedin": "https://www.linkedin.com",
                "twitter": "https://twitter.com",
                "chatgpt": "https://chat.openai.com",
                "gemini": "https://gemini.google.com",
                "perplexity": "https://www.perplexity.ai"
            }
            if site in sites:
                webbrowser.open(sites[site])
                print(f"Opening {site.capitalize()}...")
            else:
                print(f"Sorry, I don't know '{site}'. Try one of: {', '.join(sites.keys())}")

        elif command.lower().startswith("search "):
            query = command.split(" ", 1)[1]
            encoded = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded}"
            webbrowser.open(url)
            print(f"Searching Google for: {query}")

        elif command.lower().startswith("calc "):
            expression = command.split(" ", 1)[1]
            try:
                result = safe_eval(expression)
                print(f"Result: {result}")
            except Exception:
                print("Error: Invalid expression. Use only basic math (+, -, *, /, **, %)")

        elif command.lower().startswith("add "):
            task = command.split(" ", 1)[1]
            tasks.append(task)
            with open(TASKS_FILE, "w") as f:
                f.write("\n".join(tasks))
            print(f"Added task: {task}")

        elif command.lower() == "list":
            if tasks:
                print("Your tasks:")
                for i, task in enumerate(tasks, start=1):
                    print(f"{i}. {task}")
            else:
                print("No tasks yet. Add some with 'add <task>'")

        elif command.lower().startswith("done "):
            try:
                num = int(command.split(" ", 1)[1]) - 1
                if 0 <= num < len(tasks):
                    finished = tasks.pop(num)
                    with open(TASKS_FILE, "w") as f:
                        f.write("\n".join(tasks))
                    print(f"Completed task: {finished}")
                else:
                    print("Invalid task number.")
            except ValueError:
                print("Please provide a valid task number, e.g. 'done 1'")

        elif command.lower() == "clear":
            confirm = input("Are you sure you want to clear all tasks? (y/n): ").strip().lower()
            if confirm == "y":
                tasks = []
                with open(TASKS_FILE, "w") as f:
                    f.write("")  # empty file
                print("All tasks cleared!")
            else:
                print("Clear cancelled. Your tasks are safe.")

        elif command.lower() == "help":
            show_help()

        elif command.lower() == "exit":
            print("Goodbye!")
            break

        else:
            print("Sorry, I don't understand that command.")

if __name__ == "__main__":
    main()
