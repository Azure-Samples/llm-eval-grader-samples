from context import Context
from orchestrator import Orchestrator


def main():
    orchestrator = Orchestrator()
    context = Context()

    user_message = None
    while user_message != '':
        reply = orchestrator.get_reply(user_message, context)
        print(reply)
        user_message = input(">")


if __name__ == "__main__":
    main()
