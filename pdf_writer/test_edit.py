from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf_writer.editor import write_text, edit_text, extract_text

# Create a blank PDF
c = canvas.Canvas("blank.pdf", pagesize=letter)
# Add a blank page
c.showPage()
c.save()

# Add text to the blank PDF
write_text(
    input_pdf="blank.pdf",
    output_pdf="test.pdf",
    text="This is a test.",
    x=100,
    y=750,
    page=1,
    font_size=12,
)

# Edit the text in the PDF
edit_text(
    input_pdf="test.pdf",
    output_pdf="edited.pdf",
    page_num=1,
    old_text="This is a test.",
    new_text="This is an edited test.",
    font_size=12,
)

# Verify the edited text
text = extract_text("edited.pdf")
print(text)
assert "This is an edited test." in text
print("Test passed!")

