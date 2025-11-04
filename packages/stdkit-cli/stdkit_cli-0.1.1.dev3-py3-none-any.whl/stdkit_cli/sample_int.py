import stdkit
import typer
from rich import print

app = typer.Typer(add_completion=False)


@app.command()
def sample_int(
    size: int | None = typer.Argument(1, help="Specify size."),
    lower: int | None = typer.Option(0, help="Specify lower bound (included)."),
    upper: int | None = typer.Option(
        stdkit.max_signed_value(32), help="Specify upper bound (included)."
    ),
    seed: int | None = typer.Option(None, help="Specify seed."),
):
    """Print uniformly sampled random integers from the specified closed interval."""
    rng = stdkit.resolve_rng(seed)
    out = [stdkit.sample_int(lower, upper, seed=rng) for _ in range(size)]
    print(out)


if __name__ == "__main__":
    app()
