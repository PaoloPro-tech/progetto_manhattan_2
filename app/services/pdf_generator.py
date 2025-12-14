from fpdf import FPDF

class PDFReportGenerator(FPDF):
    def __init__(self, client_name, sector):
        super().__init__()
        self.client_name = client_name
        self.sector = sector
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Progetto Manhattan | Strategic Report', border=False, ln=True, align='C')
        self.ln(5)
        
        self.set_font('Helvetica', 'I', 12)
        # Safe string: rimuove caratteri non latin-1 dall'intestazione
        safe_client = self.safe_encode(self.client_name)
        safe_sector = self.safe_encode(self.sector)
        self.cell(0, 10, f"Cliente: {safe_client} ({safe_sector})", border=False, ln=True, align='C')
        self.line(10, 30, 200, 30)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def safe_encode(self, text):
        """
        Pulisce il testo da emoji e caratteri speciali che fanno crashare FPDF.
        Sostituisce i caratteri non supportati con un punto di domanda o li rimuove.
        """
        if not text:
            return ""
        # Encode in latin-1, sostituendo gli errori con '?'
        return text.encode('latin-1', 'ignore').decode('latin-1')

    def add_content(self, raw_text):
        self.add_page()
        self.set_font('Helvetica', '', 11)
        
        # Pulizia e formattazione base
        if not raw_text:
            raw_text = "Nessun contenuto generato."
            
        lines = raw_text.split('\n')
        
        for line in lines:
            safe_line = self.safe_encode(line)
            
            # Gestione Titoli (Markdown style)
            if safe_line.strip().startswith('#'):
                self.ln(4)
                self.set_font('Helvetica', 'B', 12)
                # Rimuove i cancelletti
                clean_title = safe_line.replace('#', '').strip()
                self.multi_cell(0, 8, clean_title)
                self.set_font('Helvetica', '', 11)
            
            # Gestione Bullet Points
            elif safe_line.strip().startswith('-') or safe_line.strip().startswith('*'):
                self.set_x(15) # Indenta
                self.multi_cell(0, 6, safe_line)
                self.set_x(10) # Reset indenta
            
            # Testo normale
            else:
                self.multi_cell(0, 6, safe_line)
                
            self.ln(1)

    def get_pdf_bytes(self):
        return bytes(self.output(dest='S'))