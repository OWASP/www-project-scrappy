from reportlab.pdfgen import canvas

def create_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "Hello World")
    c.drawString(100, 730, "This is a test PDF for ScrapPY.")
    c.drawString(100, 710, "Password: secret_password")
    c.drawString(100, 690, "admin")
    c.drawString(100, 670, "root")
    c.save()

if __name__ == "__main__":
    create_pdf("test.pdf")
