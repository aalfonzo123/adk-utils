from rich.prompt import Prompt


def get_password(prompt: str = "Enter password") -> str:
    """
    Prompts for a password and confirms it.

    Args:
        prompt: The prompt to display to the user.

    Returns:
        The password if it was confirmed, otherwise it exits the program.
    """
    while True:
        try:
            password = Prompt.ask(prompt, password=True)
            password_confirm = Prompt.ask("confirm", password=True)
        except (KeyboardInterrupt, EOFError):
            print("\nAborted by user.")
            exit(1)

        if password != password_confirm:
            print("Passwords do not match. Please try again.")
        else:
            return password


if __name__ == "__main__":
    password = get_password()
    print("Password successfully set.")
