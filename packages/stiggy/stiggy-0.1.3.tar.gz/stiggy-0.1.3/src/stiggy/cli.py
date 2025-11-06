import typer
from pathlib import Path
from stiggy.exporter.exporter import Exporter
from stiggy.pdf_generator.pdf_generator import PDFGenerator

app = typer.Typer(help="Stiggy: git-based engineering framework - build 1")


@app.command()
def generate_pdf():
    """
    Generate pdf report from current project.
    """
    pdf_generator = PDFGenerator()
    pdf_generator.generate()


@app.command()
def generate_md(config_file: Path):
    """
    Generate md files from yaml files.
    """
    print(f"yaml to md exporting functionality not merged yet (but existing) - doing just printout")

    exporter = Exporter(config_file)
    exporter.export()


@app.command()
def import_xlsx(xlsx_file: Path):
    """
    Placeholder import.
    """
    print(f"Importing from {xlsx_file} (functionality not implemented)")
