import typer
from fapier.commands.create import create_app
from fapier.commands.add import add

app = typer.Typer(help="FastAPI CLI Tool")
app.add_typer(create_app)
app.add_typer(add, name='add')

if __name__ == "__main__":
    app()
