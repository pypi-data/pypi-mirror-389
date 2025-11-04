import inspect
import warnings
import logging
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.traceback import install
from rich.logging import RichHandler
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from pydantic import BaseModel, Field

load_dotenv()
install(show_locals=True)
console = Console()

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_level=True,
            show_path=True
        )
    ],
)

log = logging.getLogger("rich")

# Disable noisy logs
for noisy_logger in ["httpx", "openai", "urllib3", "httpcore", "stainless_sdk"]:
    logging.getLogger(noisy_logger).setLevel(logging.CRITICAL)
    logging.getLogger(noisy_logger).propagate = False

warnings.filterwarnings("ignore")



class ErrorSuggestion(BaseModel):
    cause: str = Field(..., description="Reason why the error occurred.")
    fix: str = Field(..., description="Explanation of how to fix the error.")
    corrected_code: str = Field(..., description="AI-generated corrected version of the code.")



def openai_assist(error: str, source_code: str, args=None, kwargs=None, result=None, instruction: str = None):
    """
    Use OpenAI structured output to analyze error, suggest fixes, and return corrected code.
    """
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    instruction = os.getenv("INSTRUCTION", None)

    if not api_key:
        raise ValueError("API_KEY not found in environment variables. Please set it in your .env file.")

    client = OpenAI(api_key=api_key, base_url=base_url)

    args_repr = json.dumps(args, default=str)
    kwargs_repr = json.dumps(kwargs, default=str)

    base_prompt = (
        "You are a professional Python debugger. Your task is to analyze the given function and its error. "
        "Return structured JSON data containing three fields:\n"
        "1. cause: concise explanation of why the error happened\n"
        "2. fix: short instructions to fix it\n"
        "3. corrected_code: the corrected function version that runs without error\n\n"
        "Be accurate and keep explanations short."
    )

    if instruction:
        base_prompt += f"\nFollow this additional user instruction: {instruction}\n"

    prompt = f"""
    {base_prompt}

    Error Information:
    {error or "No exception raised"}

    Function Arguments:
    {args_repr}

    Keyword Arguments:
    {kwargs_repr}

    Function Output (if any):
    {result}

    Original Source Code:
    ```python
    {source_code}
    ```
    """

    with console.status("[bold green]Working on your code...", spinner="dots10"):
        try:
            response = client.beta.chat.completions.parse(
                model="gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": "You are a structured Python debugging assistant."},
                    {"role": "user", "content": prompt},
                ],
                response_format=ErrorSuggestion,
            )

            return response.choices[0].message.parsed

        except Exception as e:
            return {"cause": "AI suggestion unavailable", "fix": str(e)}



def catch(function):
    def wrapper(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
            return result

        except Exception as e:
            user_instruction = "Explain clearly and return fixed version of this function."
            source_code = inspect.getsource(function)

            ai_data = openai_assist(
                str(e),
                source_code,
                args,
                kwargs,
                instruction=user_instruction
            )

            console.print(Panel(Text(f"{type(e).__name__}: {e}", style="bold red"),
                                title="[bold red]Error", border_style="red"))

            console.print(Panel(Text(ai_data.cause.strip(), style="bold red"),
                                title="[bold red]Error Cause", border_style="red"))

            console.print(Panel(Text(ai_data.fix.strip(), style="bold green"),
                                title="[bold green]Fix Suggestion", border_style="green"))

            if ai_data.corrected_code:
                console.print(Panel(Text(ai_data.corrected_code.strip(), style="bold cyan"),
                                    title="[bold cyan]Correct Code", border_style="cyan"))

    return wrapper
