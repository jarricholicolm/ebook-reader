from .pdf import (
    extract_text as pdf_extract_text,
    extract_metadata as pdf_extract_metadata,
    extract_cover as pdf_extract_cover,
)
from .epub import (
    extract_text as epub_extract_text,
    extract_metadata as epub_extract_metadata,
    extract_cover as epub_extract_cover,
)
from .mobi import (
    extract_text as mobi_extract_text,
    extract_metadata as mobi_extract_metadata,
    extract_cover as mobi_extract_cover,
)
from .azw3 import (
    extract_text as azw3_extract_text,
    extract_metadata as azw3_extract_metadata,
    extract_cover as azw3_extract_cover,
)
from .djvu import (
    extract_text as djvu_extract_text,
    extract_metadata as djvu_extract_metadata,
    extract_cover as djvu_extract_cover,
)

# 创建处理器类
class PDFHandler:
    extract_text = staticmethod(pdf_extract_text)
    extract_metadata = staticmethod(pdf_extract_metadata)
    extract_cover = staticmethod(pdf_extract_cover)

class EPUBHandler:
    extract_text = staticmethod(epub_extract_text)
    extract_metadata = staticmethod(epub_extract_metadata)
    extract_cover = staticmethod(epub_extract_cover)

class MOBIHandler:
    extract_text = staticmethod(mobi_extract_text)
    extract_metadata = staticmethod(mobi_extract_metadata)
    extract_cover = staticmethod(mobi_extract_cover)

class AZW3Handler:
    extract_text = staticmethod(azw3_extract_text)
    extract_metadata = staticmethod(azw3_extract_metadata)
    extract_cover = staticmethod(azw3_extract_cover)

class DJVUHandler:
    extract_text = staticmethod(djvu_extract_text)
    extract_metadata = staticmethod(djvu_extract_metadata)
    extract_cover = staticmethod(djvu_extract_cover)

# 导出处理器
pdf = PDFHandler
epub = EPUBHandler
mobi = MOBIHandler
azw3 = AZW3Handler
djvu = DJVUHandler
