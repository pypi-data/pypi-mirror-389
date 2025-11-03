import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../../src").resolve()))


from cyclopts import App

app = App()


@app.default
def main(nome: str, idade: int):
    print("Hello World!")


if __name__ == "__main__":
    app()
