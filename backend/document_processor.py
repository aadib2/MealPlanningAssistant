"""
Document processing utilities for various file formats.
"""
from typing import Optional
import io


class DocumentProcessor:
    """
    Process various document types and extract text content.
    """
    
    def process(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Process a document and extract text.
        
        Args:
            content: Document content as bytes
            filename: Original filename
            content_type: MIME type of the document
            
        Returns:
            Extracted text content
        """
        # Determine file type
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if file_extension == 'txt' or content_type == 'text/plain':
            return self._process_text(content)
        elif file_extension == 'pdf' or content_type == 'application/pdf':
            return self._process_pdf(content)
        elif file_extension in ['doc', 'docx'] or content_type in [
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]:
            return self._process_word(content)
        elif file_extension == 'md' or content_type == 'text/markdown':
            return self._process_markdown(content)
        else:
            # Try to decode as text
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _process_text(self, content: bytes) -> str:
        """Process plain text files."""
        return content.decode('utf-8')
    
    def _process_pdf(self, content: bytes) -> str:
        """Process PDF files."""
        try:
            from pypdf import PdfReader
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("pypdf is required for PDF processing. Install with: pip install pypdf")
    
    def _process_word(self, content: bytes) -> str:
        """Process Word documents."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except ImportError:
            raise ImportError("python-docx is required for Word processing. Install with: pip install python-docx")
    
    def _process_markdown(self, content: bytes) -> str:
        """Process Markdown files."""
        return content.decode('utf-8')
