import stdkit
import typer
from rich import print

app = typer.Typer(add_completion=False)


@app.command()
def sample_int():
    """Print a random integer to stdout."""
    rnd_int = stdkit.sample_int(0, stdkit.max_signed_value(32))
    print(rnd_int)


if __name__ == "__main__":
    app()
