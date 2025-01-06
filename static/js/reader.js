class Reader {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 1;
        this.content = [];
        this.bookId = window.location.pathname.split('/').pop();
        this.theme = localStorage.getItem('reader-theme') || 'sepia';
        
        this.initElements();
        this.initEventListeners();
        this.loadContent();
        this.initDownloadButton();
        
        this.fontSize = localStorage.getItem('reader-font-size') || 'md';
        this.fontFamily = localStorage.getItem('reader-font-family') || 'serif';
        this.letterSpacing = localStorage.getItem('reader-letter-spacing') || 'normal';
        
        this.initSettings();
    }

    initElements() {
        this.contentElement = document.getElementById('readerContent');
        this.currentPageElement = document.getElementById('currentPage');
        this.totalPagesElement = document.getElementById('totalPages');
        this.prevButton = document.getElementById('prevPage');
        this.nextButton = document.getElementById('nextPage');
        this.prevButtonBottom = document.getElementById('prevPageBottom');
        this.nextButtonBottom = document.getElementById('nextPageBottom');
        this.themeToggle = document.getElementById('themeToggle');
        this.container = document.querySelector('.reader-container');
    }

    initEventListeners() {
        this.prevButton.addEventListener('click', () => this.prevPage());
        this.nextButton.addEventListener('click', () => this.nextPage());
        this.prevButtonBottom.addEventListener('click', () => this.prevPage());
        this.nextButtonBottom.addEventListener('click', () => this.nextPage());
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') this.prevPage();
            if (e.key === 'ArrowRight') this.nextPage();
        });
    }

    async loadContent() {
        try {
            this.contentElement.innerHTML = '<p class="loading">加载中...</p>';

            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/book/${this.bookId}/content`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Failed to load book content');

            const data = await response.json();
            this.content = data.content;
            this.totalPages = data.total_pages;

            this.updatePage();
        } catch (error) {
            console.error('Error loading book:', error);
            this.contentElement.innerHTML = '<p class="error">加载失败，请重试</p>';
        }
    }

    updateProgress() {
        if (!this.bookId || !this.currentPage || !this.totalPages) {
            console.error('Missing required data to update progress');
            return;
        }

        const token = localStorage.getItem('access_token');
        fetch(`/api/update/${this.bookId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                current_page: this.currentPage,
                total_pages: this.totalPages,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update progress');
                }
                return response.json();
            })
            .then(data => {
                console.log('Progress updated successfully:', data);
            })
            .catch(error => {
                console.error('Error updating progress:', error);
            });
    }

    updatePage() {
        this.contentElement.innerHTML = '';

        this.currentPageElement.textContent = this.currentPage;
        this.totalPagesElement.textContent = this.totalPages;
        this.contentElement.innerHTML = this.content[this.currentPage - 1] || '';

        this.prevButton.disabled = this.currentPage === 1;
        this.nextButton.disabled = this.currentPage === this.totalPages;
        this.prevButtonBottom.disabled = this.currentPage === 1;
        this.nextButtonBottom.disabled = this.currentPage === this.totalPages;

        this.updateProgress();
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.updatePage();
            this.scrollToTop();
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.updatePage();
            this.scrollToTop();
        }
    }

    scrollToTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    initDownloadButton() {
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadBook());
        }
    }

    async downloadBook() {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/download/${this.bookId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Download failed');
            }

            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'download';
            if (contentDisposition) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = decodeURIComponent(filename);
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Download error:', error);
            alert('下载失败，请重试');
        }
    }

    initSettings() {
        this.settingsPanel = document.getElementById('settingsPanel');
        this.settingsToggle = document.getElementById('settingsToggle');

        if (this.settingsToggle && this.settingsPanel) {
            this.settingsToggle.addEventListener('click', () => {
                this.settingsPanel.classList.toggle('show');
            });
        } else {
            console.warn('Settings elements not found, skipping settings initialization');
        }

        const fontSizeButtons = document.querySelectorAll('.size-btn');
        if (fontSizeButtons.length > 0) {
            fontSizeButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    const size = btn.dataset.size;
                    this.setFontSize(size);
                    this.updateActiveButtons('.size-btn', size);
                });
            });
        }

        const fontSelect = document.querySelector('.font-family-select');
        if (fontSelect) {
            fontSelect.addEventListener('change', (e) => {
                this.setFontFamily(e.target.value);
            });
        }

        const spacingButtons = document.querySelectorAll('.spacing-btn');
        if (spacingButtons.length > 0) {
            spacingButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    const spacing = btn.dataset.spacing;
                    this.setLetterSpacing(spacing);
                    this.updateActiveButtons('.spacing-btn', spacing);
                });
            });
        }

        const themeButtons = document.querySelectorAll('.theme-btn');
        if (themeButtons.length > 0) {
            themeButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    const theme = btn.dataset.theme;
                    this.setTheme(theme);
                    this.updateActiveButtons('.theme-btn', theme);
                });
            });
        }

        this.applySettings();
    }

    setFontSize(size) {
        this.fontSize = size;
        this.contentElement.className = `text-${size}`;
        localStorage.setItem('reader-font-size', size);
    }

    setFontFamily(family) {
        this.fontFamily = family;
        this.contentElement.classList.remove('font-serif', 'font-sans');
        this.contentElement.classList.add(`font-${family}`);
        localStorage.setItem('reader-font-family', family);
    }

    setLetterSpacing(spacing) {
        this.letterSpacing = spacing;
        this.contentElement.classList.remove('spacing-tight', 'spacing-normal', 'spacing-wide');
        this.contentElement.classList.add(`spacing-${spacing}`);
        localStorage.setItem('reader-letter-spacing', spacing);
    }

    updateActiveButtons(selector, value) {
        document.querySelectorAll(selector).forEach(btn => {
            btn.classList.toggle('active', btn.dataset.size === value || 
                                        btn.dataset.spacing === value || 
                                        btn.dataset.theme === value);
        });
    }

    applySettings() {
        this.setFontSize(this.fontSize);
        this.setFontFamily(this.fontFamily);
        this.setLetterSpacing(this.letterSpacing);

        this.updateActiveButtons('.size-btn', this.fontSize);
        this.updateActiveButtons('.spacing-btn', this.letterSpacing);
        this.updateActiveButtons('.theme-btn', this.theme);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Reader();
    document.querySelector('.reader-container').classList.add('theme-sepia');
}); 