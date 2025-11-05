// Globala variabler
let currentPage = 1;
let currentCategory = 'alla';
let currentSource = '';
let searchQuery = '';
let totalPages = 1;

// Ladda kategorier och källor
async function loadFilters() {
    try {
        const [categories, sources] = await Promise.all([
            fetch('/api/categories').then(r => r.json()),
            fetch('/api/sources').then(r => r.json())
        ]);

        const categorySelect = document.getElementById('categoryFilter');
        categories.categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
            categorySelect.appendChild(option);
        });

        const sourceSelect = document.getElementById('sourceFilter');
        sources.sources.forEach(source => {
            const option = document.createElement('option');
            option.value = source;
            option.textContent = source;
            sourceSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Fel vid laddning av filter:', error);
    }
}

// Ladda statistik
async function loadStats() {
    try {
        const stats = await fetch('/api/stats').then(r => r.json());
        document.getElementById('totalArticles').textContent = stats.total_articles;
        
        if (stats.last_update) {
            const date = new Date(stats.last_update);
            document.getElementById('lastUpdate').textContent = date.toLocaleString('sv-SE');
        }
    } catch (error) {
        console.error('Fel vid laddning av statistik:', error);
    }
}

// Ladda artiklar
async function loadArticles() {
    const loading = document.getElementById('loading');
    const grid = document.getElementById('articlesGrid');
    
    loading.style.display = 'block';
    grid.innerHTML = '';

    try {
        let url = `/api/articles?page=${currentPage}&per_page=20`;
        
        if (searchQuery) {
            url = `/api/search?q=${encodeURIComponent(searchQuery)}&page=${currentPage}&per_page=20`;
        } else {
            if (currentCategory !== 'alla') {
                url += `&category=${currentCategory}`;
            }
            if (currentSource) {
                url += `&source=${encodeURIComponent(currentSource)}`;
            }
        }

        const response = await fetch(url);
        const data = await response.json();
        
        totalPages = data.total_pages;
        
        data.articles.forEach(article => {
            const card = createArticleCard(article);
            grid.appendChild(card);
        });

        renderPagination();
    } catch (error) {
        console.error('Fel vid laddning av artiklar:', error);
        grid.innerHTML = '<p>Ett fel uppstod vid laddning av artiklar.</p>';
    } finally {
        loading.style.display = 'none';
    }
}

// Skapa artikelkort
function createArticleCard(article) {
    const card = document.createElement('div');
    card.className = 'article-card';
    card.onclick = () => window.open(article.link, '_blank');

    const publishedDate = new Date(article.published_date.$date);
    const timeAgo = getTimeAgo(publishedDate);

    card.innerHTML = `
        ${article.image_url 
            ? `<img class="article-image" src="${article.image_url}" alt="${article.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">`
            : ''}
        <div class="article-image no-image" style="${article.image_url ? 'display:none' : ''}">📄</div>
        <div class="article-content">
            <div class="article-meta">
                <span class="source">${article.source}</span>
                <span class="category-badge">${article.category}</span>
            </div>
            <h2 class="article-title">${article.title}</h2>
            <p class="article-description">${stripHtml(article.description)}</p>
            <div class="article-date">${timeAgo}</div>
        </div>
    `;

    return card;
}

// Ta bort HTML-taggar från text
function stripHtml(html) {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
}

// Beräkna tid sedan publicering
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just nu';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minuter sedan`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} timmar sedan`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)} dagar sedan`;
    
    return date.toLocaleDateString('sv-SE');
}

// Rendera paginering
function renderPagination() {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    if (totalPages <= 1) return;

    const prevBtn = document.createElement('button');
    prevBtn.textContent = '← Föregående';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            loadArticles();
            window.scrollTo(0, 0);
        }
    };
    pagination.appendChild(prevBtn);

    const pageInfo = document.createElement('button');
    pageInfo.textContent = `Sida ${currentPage} av ${totalPages}`;
    pageInfo.className = 'current-page';
    pageInfo.disabled = true;
    pagination.appendChild(pageInfo);

    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Nästa →';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadArticles();
            window.scrollTo(0, 0);
        }
    };
    pagination.appendChild(nextBtn);
}

// Event listeners
document.getElementById('categoryFilter').addEventListener('change', (e) => {
    currentCategory = e.target.value;
    currentPage = 1;
    searchQuery = '';
    document.getElementById('searchInput').value = '';
    loadArticles();
});

document.getElementById('sourceFilter').addEventListener('change', (e) => {
    currentSource = e.target.value;
    currentPage = 1;
    searchQuery = '';
    document.getElementById('searchInput').value = '';
    loadArticles();
});

let searchTimeout;
document.getElementById('searchInput').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        searchQuery = e.target.value.trim();
        currentPage = 1;
        if (searchQuery) {
            currentCategory = 'alla';
            currentSource = '';
        }
        loadArticles();
    }, 500);
});

// Initiera applikationen
loadFilters();
loadStats();
loadArticles();

// Uppdatera statistik varje minut
setInterval(loadStats, 60000);
