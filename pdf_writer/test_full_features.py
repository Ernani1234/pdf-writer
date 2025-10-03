import os
import fitz # PyMuPDF
from pdf_writer.editor import write_text, edit_text, delete_pages, reorder_pages, insert_blank_page, merge_pdfs
from pypdf import PdfReader

def create_dummy_pdf(filename="dummy.pdf", num_pages=3):
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 50), f"Página {i+1}", fontsize=24)
        if i == 0:
            page.insert_text((50, 100), "Texto Antigo para Edição", fontsize=12)
    doc.save(filename)
    doc.close()
    return filename

def run_full_tests():
    print("Iniciando testes completos...")

    # Cleanup previous test files
    for f in ["dummy.pdf", "edited_text.pdf", "deleted_page.pdf", "reordered_pages.pdf", "inserted_blank.pdf", "merged_output.pdf"]:
        if os.path.exists(f):
            os.remove(f)

    # Test 1: Create Dummy PDF
    print("Criando PDF de teste...")
    input_pdf = create_dummy_pdf()
    assert os.path.exists(input_pdf)
    print("PDF de teste criado com sucesso.")

    # Test 2: Edit Text
    print("Testando edição de texto...")
    output_edit_text = "edited_text.pdf"
    edit_text(input_pdf, output_edit_text, page_num=1, old_text="Texto Antigo para Edição", new_text="Novo Texto Editado", font_size=16, color="blue")
    assert os.path.exists(output_edit_text)
    # Verify content (manual inspection or more advanced text extraction needed for full verification)
    doc_edited = fitz.open(output_edit_text)
    text_on_page = doc_edited[0].get_text()
    assert "Novo Texto Editado" in text_on_page
    doc_edited.close()
    print("Edição de texto testada com sucesso.")

    # Test 3: Delete Pages
    print("Testando exclusão de páginas...")
    output_delete_pages = "deleted_page.pdf"
    delete_pages(input_pdf, output_delete_pages, pages_to_delete=[2]) # Delete page 2
    assert os.path.exists(output_delete_pages)
    doc_deleted = fitz.open(output_delete_pages)
    assert doc_deleted.page_count == 2 # Original 3 pages - 1 deleted = 2
    doc_deleted.close()
    print("Exclusão de páginas testada com sucesso.")

    # Test 4: Reorder Pages
    print("Testando reordenação de páginas...")
    output_reorder_pages = "reordered_pages.pdf"
    reorder_pages(input_pdf, output_reorder_pages, new_order=[3, 1, 2]) # Original: 1,2,3 -> New: 3,1,2
    assert os.path.exists(output_reorder_pages)
    doc_reordered = fitz.open(output_reorder_pages)
    assert doc_reordered.page_count == 3
    # Verify order (simple check)
    assert "Página 3" in doc_reordered[0].get_text()
    assert "Página 1" in doc_reordered[1].get_text()
    assert "Página 2" in doc_reordered[2].get_text()
    doc_reordered.close()
    print("Reordenação de páginas testada com sucesso.")

    # Test 5: Insert Blank Page
    print("Testando inserção de página em branco...")
    output_insert_blank = "inserted_blank.pdf"
    insert_blank_page(input_pdf, output_insert_blank, page_num=2) # Insert at position 2
    assert os.path.exists(output_insert_blank)
    doc_inserted = fitz.open(output_insert_blank)
    assert doc_inserted.page_count == 4 # Original 3 pages + 1 blank = 4
    # Verify blank page (check if text is minimal or absent)
    assert len(doc_inserted[1].get_text().strip()) < 10 # Should be mostly empty
    doc_inserted.close()
    print("Inserção de página em branco testada com sucesso.")

    # Test 6: Merge PDFs (using existing functionality, but good for integration)
    print("Testando mesclagem de PDFs...")
    pdf_to_merge1 = create_dummy_pdf("merge_part1.pdf", 1)
    pdf_to_merge2 = create_dummy_pdf("merge_part2.pdf", 1)
    output_merged = "merged_output.pdf"
    merge_pdfs([pdf_to_merge1, pdf_to_merge2], output_merged)
    assert os.path.exists(output_merged)
    doc_merged = fitz.open(output_merged)
    assert doc_merged.page_count == 2
    doc_merged.close()
    os.remove(pdf_to_merge1)
    os.remove(pdf_to_merge2)
    print("Mesclagem de PDFs testada com sucesso.")

    print("Todos os testes completos foram executados com sucesso!")

if __name__ == "__main__":
    run_full_tests()

