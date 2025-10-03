from __future__ import annotations

import json
from typing import List, Optional

import typer
from rich import print

from . import (
    write_text,
    add_image,
    sign_pdf,
    merge_pdfs,
    split_pdf,
    rotate_pages,
    extract_text,
    fill_form,
    flatten_form,
    edit_text,
    delete_pages,
    reorder_pages,
    insert_blank_page,
)
from .gui import run_gui
from reportlab.lib.pagesizes import letter

app = typer.Typer(help="Editor de PDFs: escrever, assinar, mesclar, dividir, girar, extrair texto e preencher formulários.")


@app.command()
def write_text_cmd(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    text: str = typer.Option(..., help="Texto a escrever"),
    x: float = typer.Option(..., help="Posição X (pt)"),
    y: float = typer.Option(..., help="Posição Y (pt)"),
    page: int = typer.Option(1, help="Número da página (1-based)"),
    font_name: str = typer.Option("Helvetica", help="Nome da fonte ou caminho .ttf"),
    size: int = typer.Option(12, help="Tamanho da fonte"),
    color: str = typer.Option("black", help="Cor do texto (ex: black, red)"),
):
    write_text(input, output, text, x, y, page, font_name, size, color)
    print(f"[green]Texto inserido em[/green] {output}")


@app.command()
def edit_text_cmd(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    page_num: int = typer.Option(..., help="Número da página (1-based)"),
    old_text: str = typer.Option(..., help="Texto existente a ser substituído"),
    new_text: str = typer.Option(..., help="Novo texto"),
    font_name: Optional[str] = typer.Option(None, help="Nome da fonte (opcional)"),
    font_size: Optional[float] = typer.Option(None, help="Tamanho da fonte (opcional)"),
    color: Optional[str] = typer.Option(None, help="Cor do texto (opcional)"),
):
    edit_text(input, output, page_num, old_text, new_text, font_name, font_size, color)
    print(f"[green]Texto editado em[/green] {output}")


@app.command()
def add_image_cmd(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    image: str = typer.Option(..., help="Caminho da imagem"),
    x: float = typer.Option(..., help="Posição X"),
    y: float = typer.Option(..., help="Posição Y"),
    width: Optional[float] = typer.Option(None, help="Largura"),
    height: Optional[float] = typer.Option(None, help="Altura"),
    page: int = typer.Option(1, help="Página (1-based)"),
):
    add_image(input, output, image, x, y, width, height, page)
    print(f"[green]Imagem inserida em[/green] {output}")


@app.command()
def sign(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    image: str = typer.Option(..., help="Imagem de assinatura"),
    page: int = typer.Option(-1, help="Página (1-based), -1 = última"),
    margin_x: float = typer.Option(36, help="Margem X"),
    margin_y: float = typer.Option(36, help="Margem Y"),
    width: float = typer.Option(180, help="Largura da assinatura (pt)"),
):
    sign_pdf(input, output, image, page, margin_x, margin_y, width)
    print(f"[green]Assinatura aplicada em[/green] {output}")


@app.command()
def merge(
    inputs: List[str] = typer.Argument(..., help="Lista de PDFs a mesclar"),
    output: str = typer.Option(..., help="PDF de saída"),
):
    merge_pdfs(inputs, output)
    print(f"[green]PDFs mesclados em[/green] {output}")


@app.command()
def split(
    input: str = typer.Option(..., help="PDF de entrada"),
    ranges: str = typer.Option(..., help="Intervalos, ex: \"1-3,5\""),
    output_dir: str = typer.Option("output", help="Diretório de saída"),
):
    split_pdf(input, ranges, output_dir)
    print(f"[green]Páginas salvas em[/green] {output_dir}")


@app.command()
def rotate(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    degrees: int = typer.Option(..., help="Rotação em graus (90, 180, 270)"),
    pages: Optional[List[int]] = typer.Argument(None, help="Páginas (1-based). Se omitido, todas."),
):
    rotate_pages(input, output, degrees, pages)
    print(f"[green]PDF salvo em[/green] {output}")


@app.command("extract-text")
def extract_text_cmd(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: Optional[str] = typer.Option(None, help="Arquivo .txt opcional"),
    pages: Optional[List[int]] = typer.Argument(None, help="Páginas (1-based). Se omitido, todas."),
):
    text = extract_text(input, pages)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[green]Texto extraído para[/green] {output}")
    else:
        print(text)


@app.command("fill-form")
def fill_form_cmd(
    input: str = typer.Option(..., help="PDF com formulário"),
    output: str = typer.Option(..., help="PDF preenchido"),
    data: str = typer.Option(..., help="JSON com campos e valores"),
    flatten: bool = typer.Option(False, "--flatten", is_flag=True, help="Achatar após preencher"),
):
    payload = json.loads(data)
    fill_form(input, output, payload, flatten)
    print(f"[green]Formulário preenchido em[/green] {output}")


@app.command()
def flatten(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
):
    flatten_form(input, output)
    print(f"[green]Formulário achatado em[/green] {output}")


@app.command()
def delete_pages_cmd(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    pages: List[int] = typer.Argument(..., help="Números das páginas a serem excluídas (1-based)"),
):
    delete_pages(input, output, pages)
    print(f"[green]Páginas excluídas em[/green] {output}")


@app.command()
def reorder_pages_cmd(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    order: List[int] = typer.Argument(..., help="Nova ordem das páginas (1-based), ex: 3 1 2"),
):
    reorder_pages(input, output, order)
    print(f"[green]Páginas reordenadas em[/green] {output}")


@app.command()
def insert_blank_page_cmd(
    input: str = typer.Option(..., help="PDF de entrada"),
    output: str = typer.Option(..., help="PDF de saída"),
    page_num: int = typer.Option(..., help="Número da página antes da qual a página em branco será inserida (1-based)"),
    width: float = typer.Option(letter[0], help="Largura da página em branco (pt)"),
    height: float = typer.Option(letter[1], help="Altura da página em branco (pt)"),
):
    insert_blank_page(input, output, page_num, width, height)
    print(f"[green]Página em branco inserida em[/green] {output}")


@app.command()
def gui():
    """Abrir interface gráfica avançada."""
    run_gui()


if __name__ == "__main__":
    app()

