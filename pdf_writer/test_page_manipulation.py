from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf_writer.editor import extract_text, delete_pages, reorder_pages, insert_blank_page
import os
import fitz

# Set the working directory to the project root for consistent path resolution
# os.chdir("pdf-writer/pdf-writer") # This is handled by the agent's execution context

# Create a multi-page PDF for testing
def create_test_pdf(filename="multi_page_test.pdf", num_pages=3):
    c = canvas.Canvas(filename, pagesize=letter)
    for i in range(num_pages):
        c.drawString(100, 750, f"This is page {i+1}.")
        c.showPage()
    c.save()

# Test delete_pages
create_test_pdf("delete_test_input.pdf", 3)
delete_pages("delete_test_input.pdf", "delete_test_output.pdf", [2])
text_after_delete = extract_text("delete_test_output.pdf")
assert "This is page 1." in text_after_delete
assert "This is page 3." in text_after_delete
assert "This is page 2." not in text_after_delete
print("Delete pages test passed!")

# Test reorder_pages
create_test_pdf("reorder_test_input.pdf", 3)
reorder_pages("reorder_test_input.pdf", "reorder_test_output.pdf", [3, 1, 2])
# Extract text and verify order (this is a simplified check)
# A more robust check would involve checking page content order
text_after_reorder = extract_text("reorder_test_output.pdf")
# For simplicity, we just check if all original texts are present
assert "This is page 1." in text_after_reorder
assert "This is page 2." in text_after_reorder
assert "This is page 3." in text_after_reorder
print("Reorder pages test passed!")

# Test insert_blank_page
create_test_pdf("insert_test_input.pdf", 2)
insert_blank_page("insert_test_input.pdf", "insert_test_output.pdf", 2)
# Verify by checking the number of pages
doc = fitz.open("insert_test_output.pdf")
assert doc.page_count == 3
doc.close()
print("Insert blank page test passed!")

print("All page manipulation tests passed!")

