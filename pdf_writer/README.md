# PDF Writer (Editor de PDFs)

Ferramenta em Python para editar PDFs: escrever texto, incluir assinaturas/imagens, mesclar, dividir, girar, extrair texto e preencher formulários.

## Instalação

1. Requisitos: Python 3.9+
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Uso Rápido (CLI)

- Escrever texto em uma página específica:
  ```bash
  python -m pdf_writer.cli write-text --input input.pdf --output out.pdf \
    --text "Assinado por Fulano" --x 72 --y 100 --page 1 --size 12
  ```

- Inserir imagem (assinatura) em uma página:
  ```bash
  python -m pdf_writer.cli add-image --input input.pdf --output out.pdf \
    --image assinatura.png --x 420 --y 72 --width 150 --height 60 --page 1
  ```

- Assinar rapidamente (coloca imagem no canto inferior direito):
  ```bash
  python -m pdf_writer.cli sign --input input.pdf --output out.pdf --image assinatura.png
  ```

- Mesclar PDFs:
  ```bash
  python -m pdf_writer.cli merge --inputs a.pdf b.pdf c.pdf --output merged.pdf
  ```

- Dividir por intervalos (ex: 1-3,5):
  ```bash
  python -m pdf_writer.cli split --input merged.pdf --ranges "1-3,5" --output-dir parts
  ```

- Girar páginas 90°:
  ```bash
  python -m pdf_writer.cli rotate --input input.pdf --output out.pdf --degrees 90 --pages 1 2 3
  ```

- Extrair texto:
  ```bash
  python -m pdf_writer.cli extract-text --input input.pdf --output out.txt
  ```
- Preencher formulário:
  ```bash
  python -m pdf_writer.cli fill-form --input form.pdf --output filled.pdf --data '{"nome":"Fulano","cpf":"000.000.000-00"}'
  ```

- Achatar formulário:
  ```bash
  python -m pdf_writer cli flatten --input filled.pdf --output flattened.pdf
  ```

## Observações

- Coordenadas `x`/`y` em pontos PostScript (72 pt ≈ 1 inch). Origem no canto inferior esquerdo.
- Páginas são 1-based no CLI. Internamente convertemos para 0-based.
- Para melhor qualidade de assinatura, use imagens PNG com fundo transparente.

## Interface Gráfica (GUI)

Agora o projeto inclui uma GUI avançada baseada em PySide6 com visualizador embutido de PDF.

### Como iniciar

No diretório do projeto:

```bash
python -m pdf_writer gui
```

Se aparecer erro de módulo PySide6 ausente, rode novamente a instalação:

```bash
pip install -r requirements.txt
```

### Funcionalidades na GUI

- Abrir e visualizar PDF (visualização multipágina, zoom Fit Width/Fit Page/Custom).
- Adicionar texto: escolha texto, tamanho e cor; clique na página para posicionar.
- Adicionar imagem/assinatura: escolha imagem e largura; clique para posicionar.
- Assinatura rápida: aplica imagem no canto inferior direito e salva.
- Girar todas as páginas e salvar.
- Extrair texto do documento para arquivo .txt.
- Flatten (achatar) formulários.
- Salvar como: aplica todas as edições em lote e salva em novo PDF.

Observação: o mapeamento de clique para coordenadas do PDF é aproximado (ajustado pelo tamanho do widget). Para uso preciso (carimbos em posições exatas), use o CLI ou ajuste fino com zoom alto na GUI.
