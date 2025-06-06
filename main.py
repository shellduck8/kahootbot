import asyncio
import random

from kahoot import KahootClient  # Make sure this is the correct import for your library
from kahoot.packets.impl.respond import RespondPacket
from kahoot.packets.server.game_over import GameOverPacket
from kahoot.packets.server.game_start import GameStartPacket
from kahoot.packets.server.question_end import QuestionEndPacket
from kahoot.packets.server.question_ready import QuestionReadyPacket
from kahoot.packets.server.question_start import QuestionStartPacket


async def handle_question_start(packet: QuestionStartPacket, client_instance: KahootClient, bot_name: str):
    question_number: int = packet.game_block_index
    await asyncio.sleep(0.1)
    try:
        await client_instance.send_packet(RespondPacket(client_instance.game_pin, random.randint(0, 3), question_number))
    except Exception as e:
        print(f"[{bot_name}] ERROR while sending answer to question: {e}")


async def handle_question_ready(packet: QuestionReadyPacket, bot_name: str):
    print(f"[{bot_name}] Ready for question {packet.question_index + 1}.")


async def run_single_bot(game_pin: int, bot_base_name: str, bot_number: int):
    client = KahootClient()
    bot_name = f"{bot_base_name}{bot_number}"

    # Register event handlers
    client.on("question_start", lambda packet: handle_question_start(packet, client, bot_name))
    client.on("question_ready", lambda packet: handle_question_ready(packet, bot_name))

    try:
        print(f"[{bot_name}] Attempting to join game {game_pin}...")
        # If `join_game` is blocking and keeps the connection alive,
        # this coroutine will "hang" here for the duration of the game.
        # Event handlers will be triggered by the asyncio event loop.
        await client.join_game(game_pin, bot_name)
        # The line below probably won't execute if `join_game` is long-running.
        # Confirmation of joining should come from an event (e.g., handled in handle_game_start).
        # print(f"[{bot_name}] Line after `await client.join_game` (may not execute).")
    except asyncio.CancelledError:
        print(f"[{bot_name}] Join task cancelled.")  # In case the task was cancelled
    except Exception as e:
        print(f"[{bot_name}] ERROR during `join_game` or disconnect: {e}")
    finally:
        # You could add cleanup logic here, e.g., client.close(), if the library requires it
        # print(f"[{bot_name}] Coroutine run_single_bot finished.")
        pass


async def main():
    while True:
        game_pin_str = input("Enter game PIN: ")
        if game_pin_str.isdigit():
            game_pin = int(game_pin_str)
            break
        else:
            print("Invalid PIN. The PIN should consist only of digits.")

    while True:
        num_bots_str = input("Enter number of bots to launch: ")
        if num_bots_str.isdigit() and int(num_bots_str) > 0:
            number_of_bots = int(num_bots_str)
            break
        else:
            print("Invalid number of bots. Please enter a positive integer.")

    bot_base_name_input = input("Enter base name for bots (e.g., Ben): ")
    if not bot_base_name_input.strip():
        bot_base_name_input = "Bot"
        print(f"Default base name used: '{bot_base_name_input}'")

    print(f"\nInitializing {number_of_bots} bots with names '{bot_base_name_input} X' (one by one)...")

    active_bot_tasks = []

    for i in range(number_of_bots):
        bot_number = i + 1
        print(f"\n--- Initializing bot: {bot_base_name_input} {bot_number} ---")

        # Create a task for each bot. It will attempt to join in the background.
        task = asyncio.create_task(run_single_bot(game_pin, bot_base_name_input, bot_number))
        active_bot_tasks.append(task)

        # Wait a bit to give the current bot time to initiate joining
        # before starting the next. This causes bots to *begin* joining
        # one-by-one in the player list.
        print(f"Bot {bot_base_name_input} {bot_number} started in background. Waiting for next one...")
        if i < number_of_bots - 1:  # Don't wait after the last bot
            # This `sleep` controls how quickly we *start* each bot.
            # Adjust this to achieve desired effect for bot appearance.
            await asyncio.sleep(0.2)  # e.g., 2 seconds delay between initiations

    print(f"\nInitialization of {number_of_bots} bots complete.")
    print("Bots are now active and waiting for game events.")
    print("Press Ctrl+C to stop all bots.")

    # Wait for all bot tasks to finish.
    # They will finish when their `run_single_bot` coroutines end
    # (e.g., after receiving `game_over` or encountering an error).
    if active_bot_tasks:
        await asyncio.gather(*active_bot_tasks, return_exceptions=True)

    print("\nAll bot tasks have ended.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
    except Exception as e:
        print(f"Unexpected error in main execution: {e}")
