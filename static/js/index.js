document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // 加载分类
    loadCategories();

    // 绑定上传表单事件
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }

    // 绑定搜索表单事件
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }

    // 绑定添加书籍按钮点击事件
    const uploadBtn = document.querySelector('.upload-btn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', openModal);
    }

    checkTokenExpiration();

    // 绑定返回按钮事件
    const backButton = document.getElementById('backButton');
    if (backButton) {
        backButton.addEventListener('click', backToCategories);
    }

    // 绑定分类按钮点击事件
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const categoryId = btn.dataset.categoryId;
            const categoryName = btn.textContent.trim();
            switchToBookList(categoryId, categoryName);
        });
    });

    initSearch();
    initPagination();
    initSortButtons();
});

// 加载分类
async function loadCategories() {
    try {
        console.log('Loading categories...');
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/categories', {
            headers: {
                'Authorization': `Bearer ${token}`
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to load categories');
        }

        const data = await response.json();
        console.log('Categories data:', data);  // 查看返回的分类数据
        
        // 更新分类列表
        updateCategories(data.categories);
        
        // 更新上传模态框中的分类选项
        const categorySelect = document.getElementById('category');
        if (categorySelect) {
            categorySelect.innerHTML = data.categories.map(category => 
                `<option value="${category.id}">${category.name}</option>`
            ).join('');
        }
        
        // 更新统计信息
        console.log('Updating stats with categories:', data.categories);
        updateCategoryStats(data.categories);
    } catch (error) {
        console.error('Error loading categories:', error);
        const categoriesContainer = document.querySelector('.categories');
        if (categoriesContainer) {
            categoriesContainer.innerHTML = '<div class="error">加载分类失败</div>';
        }
    }
}

// 更新分类显示
function updateCategories(categories) {
    const categoriesContainer = document.querySelector('.categories');
    
    // 添加"全部"分类
    let html = `
        <a href="#" 
           class="category-btn" 
           data-category-id="all">
            全部
        </a>
    `;

    // 添加其他分类
    categories.forEach(category => {
        html += `
            <a href="#" 
               class="category-btn" 
               data-category-id="${category.id}">
                ${category.name}
                ${category.book_count > 0 ? `<span class="count">(${category.book_count})</span>` : ''}
            </a>
        `;
    });

    categoriesContainer.innerHTML = html;

    // 绑定分类按钮点击事件
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const categoryId = btn.dataset.categoryId;
            const categoryName = btn.textContent.trim();
            switchToBookList(categoryId, categoryName);
        });
    });
}

// 分页相关变量
let currentPage = 1;
const booksPerPage = 4;  // 修改为4本书每页
let totalBooks = 0;

// 加载书籍
async function loadBooks(category = 'all', sort = 'recent', search = '', page = 1) {
    try {
        const token = localStorage.getItem('access_token');
        const url = new URL('/api/search_by_category', window.location.origin);
        url.searchParams.set('category', category);
        url.searchParams.set('sort', sort);
        url.searchParams.set('page', page);
        url.searchParams.set('per_page', booksPerPage);
        if (search) {
            url.searchParams.set('search', search);
        }

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load books');
        }

        const data = await response.json();
        updateBookList(data.books);
        updatePagination(data.total, page);
    } catch (error) {
        console.error('Error loading books:', error);
    }
}

// 更新分页信息
function updatePagination(total, currentPage) {
    totalBooks = total;
    const totalPages = Math.ceil(total / booksPerPage);
    
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages;
    
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
}

// 初始化分页事件监听
function initPagination() {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            // 获取当前激活的分类
            const activeCategory = document.querySelector('.category-btn.active');
            const categoryId = activeCategory ? activeCategory.dataset.categoryId : 'all';
            loadCategoryBooks(categoryId);
        }
    });
    
    nextBtn.addEventListener('click', () => {
        const totalPages = Math.ceil(totalBooks / booksPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            // 获取当前激活的分类
            const activeCategory = document.querySelector('.category-btn.active');
            const categoryId = activeCategory ? activeCategory.dataset.categoryId : 'all';
            loadCategoryBooks(categoryId);
        }
    });
}

// 更新书籍列表显示
function updateBookList(books) {
    const bookListContainer = document.querySelector('#bookListView .book-list');
    const categoryView = document.getElementById('categoryView');
    const bookListView = document.getElementById('bookListView');
    
    // 切换视图
    categoryView.style.display = 'none';
    bookListView.style.display = 'block';
    
    if (!books || books.length === 0) {
        bookListContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-books"></i>
                <h3>未找到相关书籍</h3>
                <p>试试其他关键词，或者点击右上角的"添加书籍"添加一本吧</p>
            </div>
        `;
        return;
    }

    bookListContainer.innerHTML = books.map(book => `
        <div class="book-item" onclick="openReader(${book.id})">
            <div class="book-cover">
                ${book.cover_image_url 
                    ? `<img src="/api/cover/${encodeURIComponent(book.cover_image_url)}" alt="${book.title}" loading="lazy"/>` 
                    : `<div class="default-cover">
                          <i class="fas fa-book"></i>
                          <span>${book.title.slice(0, 2)}</span>
                       </div>`
                }
            </div>
            <div class="book-info">
                <div class="book-info-left">
                    <h3 class="book-title" title="${book.title}">${book.title}</h3>
                    <p class="book-author">${book.author}</p>
                    <p class="book-language">${book.language || '未知语言'}</p>
                    <p class="book-description">${book.description || '暂无描述'}</p>
                </div>
            </div>
        </div>
    `).join('');

    // 显示返回按钮
    const backButton = document.getElementById('backButton');
    if (backButton) {
        backButton.style.display = 'block';
    }
}

// 添加打开阅读器的函数
function openReader(bookId) {
    window.location.href = `/reader/${bookId}`;
}

// 视图切换
const viewButtons = document.querySelectorAll('.view-btn');
const bookList = document.querySelector('.book-list');

viewButtons.forEach(btn => {
    btn.addEventListener('click', function() {
        const view = this.dataset.view;
        viewButtons.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        bookList.className = `book-list ${view}-view`;
        localStorage.setItem('bookListView', view);
    });
});

// 搜索防抖
let searchTimeout;

// 初始化搜索功能
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchForm = document.getElementById('searchForm');

    // 处理表单提交
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault(); // 阻止表单默认提交
        handleSearch(searchInput.value); // 直接传递搜索词
    });

    // 处理输入事件（实时搜索）
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            handleSearch(e.target.value);
        }, 500);
    });
}

// 处理搜索
async function handleSearch(searchTerm) {
    try {
        // 更新 URL 参数但不刷新页面
        const url = new URL(window.location.href);
        url.searchParams.set('search', searchTerm);
        window.history.pushState({}, '', url);

        // 获取当前分类和排序方式
        const category = url.searchParams.get('category') || 'all';
        const sort = url.searchParams.get('sort') || 'recent';

        // 加载搜索结果
        await loadBooks(category, sort, searchTerm);

        // 更新分类按钮状态
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.categoryId === category) {
                btn.classList.add('active');
            }
        });
    } catch (error) {
        console.error('Search error:', error);
    }
}

async function uploadBook(input) {
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];
    if (!file.name.match(/\.(pdf|epub|mobi|azw3|djvu)$/i)) {
        alert('只支持 PDF、EPUB、MOBI、AZW3 和 DJVU 格式的文件');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // 获取用户填写的自定义信息
    const title = document.querySelector('#book-title').value.trim();
    const author = document.querySelector('#book-author').value.trim();
    const description = document.querySelector('#book-description').value.trim();
    const language = document.querySelector('#book-language').value.trim();
    const category = document.querySelector('#book-category').value.trim();
    const cover = document.querySelector('#custom-cover').files[0];

    if (title) formData.append('title', title);
    if (author) formData.append('author', author);
    if (description) formData.append('description', description);
    if (language) formData.append('language', language);
    formData.append('category_id', category || 1);
    if (cover) formData.append('cover', cover);

    const uploadBtn = document.querySelector('.upload-btn');
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 上传中...';

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            credentials: 'include',
            body: formData,
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || '上传失败');
        }
        alert('上传成功！');
        window.location.reload();
    } catch (error) {
        console.error('Upload error:', error);
        if (error.message.includes('Token has expired')) {
            alert('登录已过期，请重新登录');
            window.location.href = '/login';
        } else {
            alert('上传失败: ' + error.message);
        }
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-plus"></i> 添加书籍';
        input.value = '';
    }
}


// 阅读书籍
function readBook(bookId) {
    window.location.href = `/reader/${bookId}`;
}

// 更新统计数据
function updateBookStats() {
    const books = document.querySelectorAll('.book-card');
    const readingBooks = Array.from(books).filter(book => {
        const progress = parseInt(book.dataset.progress || 0);
        return progress > 0 && progress < 100;
    });
    const finishedBooks = Array.from(books).filter(book => {
        const progress = parseInt(book.dataset.progress || 0);
        return progress === 100;
    });

    document.querySelector('.stat-value:nth-child(1)').textContent = books.length;
    document.querySelector('.stat-value:nth-child(2)').textContent = readingBooks.length;
    document.querySelector('.stat-value:nth-child(3)').textContent = finishedBooks.length;
}

function updateSort(value) {
    const url = new URL(window.location);
    url.searchParams.set('sort', value);
    window.location = url;
}

// 清除搜索
function clearSearch() {
    const url = new URL(window.location);
    url.searchParams.delete('search');
    window.location = url;
}

// 退出登录
function logout() {
    // 清除所有token
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // 清除cookie
    document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = 'refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    
    // 跳转到登录页
    window.location.href = '/login';
}

// 添加token过期检查
function checkTokenExpiration() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        // 检查cookie中是否有token
        const cookieToken = document.cookie
            .split('; ')
            .find(row => row.startsWith('access_token='))
            ?.split('=')[1];
            
        if (!cookieToken) {
            window.location.href = '/login';
            return;
        }
        // 如果cookie中有token，保存到localStorage
        localStorage.setItem('access_token', cookieToken);
        return;
    }

    // 解析token
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expTime = payload.exp * 1000; // 转换为毫秒
        
        // 如果token已过期或即将过期（5分钟内）
        if (Date.now() >= expTime - 300000) {
            alert('登录已过期，请重新登录');
            logout();
        }
    } catch (e) {
        console.error('Token parsing error:', e);
        // 不要立即登出，可能是解析错误
        console.log('Token parse failed, will try to continue...');
    }
}

// 更新分类统计
function updateCategoryStats(categories) {
    const categoryStatsContainer = document.querySelector('.category-stats');
    if (categoryStatsContainer) {
        // 计算总藏书数
        const totalBooks = categories.reduce((sum, category) => sum + category.book_count, 0);
        
        // 更新总藏书数显示
        const totalBooksElement = document.querySelector('.total-books .stat-value');
        if (totalBooksElement) {
            totalBooksElement.textContent = totalBooks;
        }
        
        // 生成分类卡片，添加点击事件
        const html = categories.map(category => `
            <div class="stat-item" onclick="switchToBookList(${category.id}, '${category.name}')">
                <i class="fas fa-book-open"></i>
                <div class="stat-info">
                    <span class="stat-value">${category.book_count}</span>
                    <span class="stat-label">${category.description || category.name}</span>
                </div>
            </div>
        `).join('');
        
        categoryStatsContainer.innerHTML = html;
    }
}

// 切换到书籍列表视图
async function switchToBookList(categoryId, categoryName) {
    // 更新UI状态
    document.getElementById('categoryView').style.display = 'none';
    document.getElementById('bookListView').style.display = 'block';
    document.getElementById('backButton').style.display = 'inline-block';
    
    // 更新分类按钮的激活状态
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.categoryId === categoryId.toString()) {
            btn.classList.add('active');
        }
    });

    // 重置分页状态
    currentPage = 1;
    
    // 加载该分类的书籍
    await loadCategoryBooks(categoryId);
}

// 返回分类视图
function backToCategories() {
    const categoryView = document.getElementById('categoryView');
    const bookListView = document.getElementById('bookListView');
    const backButton = document.getElementById('backButton');
    
    categoryView.style.display = 'block';
    bookListView.style.display = 'none';
    backButton.style.display = 'none';

    // 清除搜索框
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = '';
    }

    // 更新 URL
    const url = new URL(window.location.href);
    url.searchParams.delete('search');
    window.history.pushState({}, '', url);
}

// 加载分类的书籍
async function loadCategoryBooks(categoryId) {
    try {
        const token = localStorage.getItem('access_token');
        const url = new URL(`/api/category/${categoryId}/books`, window.location.origin);
        
        // 添加分页和排序参数
        url.searchParams.set('page', currentPage);
        url.searchParams.set('per_page', booksPerPage);
        url.searchParams.set('sort', currentSort);

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load books');
        }

        const data = await response.json();
        updateBookList(data.books);
        updatePagination(data.total, data.page);
    } catch (error) {
        console.error('Error loading books:', error);
        alert('加载书籍失败，请重试');
    }
}

// 打开模态框
function openModal() {
    document.getElementById('uploadModal').style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

// 处理上传表单提交
async function handleUpload(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '上传失败');
        }

        const result = await response.json();
        alert('上传成功！');
        closeModal();
        
        // 重新加载分类统计和书籍列表
        await loadCategories();  // 更新分类统计
        
        // 清空表单
        form.reset();
    } catch (error) {
        console.error('Upload error:', error);
        alert(`上传失败: ${error.message}`);
    }
}

// 添加排序状态变量
let currentSort = 'recent';

// 初始化排序按钮
function initSortButtons() {
    const sortButtons = document.querySelectorAll('.sort-btn');
    sortButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // 更新按钮状态
            sortButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 获取排序方式
            currentSort = btn.dataset.sort;
            
            // 重置页码并重新加载书籍
            currentPage = 1;
            
            // 获取当前分类
            const activeCategory = document.querySelector('.category-btn.active');
            const categoryId = activeCategory ? activeCategory.dataset.categoryId : 'all';
            loadCategoryBooks(categoryId);
        });
    });
}
