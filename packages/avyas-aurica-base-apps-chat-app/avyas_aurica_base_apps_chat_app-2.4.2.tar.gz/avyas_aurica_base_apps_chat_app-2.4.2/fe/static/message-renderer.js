/**
 * Dynamic Rendering System for Chat Messages
 * Handles different data types and renders them appropriately
 * Supports loading app-specific renderers dynamically
 */

class MessageRenderer {
    constructor() {
        this.appRenderers = new Map(); // Store app-specific renderers
        this.renderTypes = {
            'text': this.renderText.bind(this),
            'markdown': this.renderMarkdown.bind(this),
            'code': this.renderCode.bind(this),
            'json': this.renderJson.bind(this),
            'profile_card': this.renderProfileCard.bind(this),
            'table': this.renderTable.bind(this),
            'list': this.renderList.bind(this),
            'execution_status': this.renderExecutionStatus.bind(this),
            'success': this.renderSuccess.bind(this),
            'error': this.renderError.bind(this),
            'warning': this.renderWarning.bind(this),
            'info': this.renderInfo.bind(this)
        };
    }

    /**
     * Register an app-specific renderer
     */
    registerAppRenderer(renderer) {
        if (!renderer.name) {
            console.error('Renderer must have a name property');
            return false;
        }
        
        this.appRenderers.set(renderer.name, renderer);
        console.log(`✅ Registered renderer for: ${renderer.name}`);
        return true;
    }

    /**
     * Main render method - delegates to specific renderers based on block type
     */
    render(message) {
        const container = document.createElement('div');
        container.className = 'message-renderer';

        // Check if message has render blocks
        if (message.render_blocks && message.render_blocks.length > 0) {
            console.log('🎨 Rendering message with blocks:', message.render_blocks);
            
            // Render using structured blocks
            message.render_blocks.forEach((block, index) => {
                console.log(`  Block ${index}:`, block.type, block.data);
                const blockEl = this.renderBlock(block);
                if (blockEl) {
                    container.appendChild(blockEl);
                } else {
                    console.warn(`  ⚠️ Block ${index} returned null`);
                }
            });
        } else {
            console.log('ℹ️ No render_blocks, using fallback');
            // Fallback to plain text rendering
            const textBlock = {
                type: 'markdown',
                data: { content: message.content },
                metadata: {}
            };
            container.appendChild(this.renderBlock(textBlock));
        }

        return container;
    }

    /**
     * Render a single block based on its type
     * First checks app-specific renderers, then falls back to built-in renderers
     */
    renderBlock(block) {
        console.log(`🔍 Rendering block type: ${block.type}`);
        
        // Try app-specific renderers first
        for (const [appName, appRenderer] of this.appRenderers) {
            if (typeof appRenderer.canRender === 'function') {
                const canRender = appRenderer.canRender(block.data, block.metadata);
                if (canRender) {
                    console.log(`🎨 Using ${appName} renderer for block`);
                    const rendered = appRenderer.render(block);
                    if (rendered) return rendered;
                }
            }
        }
        
        // Fall back to built-in renderers
        const renderer = this.renderTypes[block.type];
        if (renderer) {
            return renderer(block.data, block.metadata);
        } else {
            console.warn(`Unknown render type: ${block.type}`);
            return this.renderText(block.data, block.metadata);
        }
    }

    /**
     * Render plain text
     */
    renderText(data, metadata) {
        const div = document.createElement('div');
        div.className = 'render-text';
        div.textContent = data.content || '';
        return div;
    }

    /**
     * Render markdown (basic support)
     */
    renderMarkdown(data, metadata) {
        const div = document.createElement('div');
        div.className = 'render-markdown';
        
        let html = data.content || '';
        
        // Basic markdown parsing
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
        
        // Italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/_(.*?)_/g, '<em>$1</em>');
        
        // Code inline
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Line breaks
        html = html.replace(/\n/g, '<br>');
        
        div.innerHTML = html;
        return div;
    }

    /**
     * Render code block
     */
    renderCode(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-code';
        
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        
        if (metadata && metadata.language) {
            code.className = `language-${metadata.language}`;
        }
        
        code.textContent = data.content || '';
        pre.appendChild(code);
        container.appendChild(pre);
        
        return container;
    }

    /**
     * Render JSON data
     */
    renderJson(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-json';
        
        const pre = document.createElement('pre');
        const code = document.createElement('code');
        code.className = 'language-json';
        
        try {
            const jsonContent = typeof data.content === 'string' 
                ? data.content 
                : JSON.stringify(data.content, null, 2);
            code.textContent = jsonContent;
        } catch (e) {
            code.textContent = String(data.content);
        }
        
        pre.appendChild(code);
        container.appendChild(pre);
        
        return container;
    }

    /**
     * Render profile card
     */
    renderProfileCard(data, metadata) {
        const card = document.createElement('div');
        card.className = 'render-profile-card';
        
        const content = data.content || {};
        
        card.innerHTML = `
            <div class="profile-header">
                <div class="profile-avatar">
                    <i class="bi bi-person-circle"></i>
                </div>
                <div class="profile-info">
                    <h3 class="profile-name">${this.escapeHtml(content.display_name || content.username || 'Unknown')}</h3>
                    <p class="profile-username">@${this.escapeHtml(content.username || 'unknown')}</p>
                </div>
            </div>
            <div class="profile-details">
                ${content.email ? `
                    <div class="profile-field">
                        <i class="bi bi-envelope"></i>
                        <span>${this.escapeHtml(content.email)}</span>
                    </div>
                ` : ''}
                ${content.role ? `
                    <div class="profile-field">
                        <i class="bi bi-shield-check"></i>
                        <span class="role-badge">${this.escapeHtml(content.role)}</span>
                    </div>
                ` : ''}
                ${content.mobile_number ? `
                    <div class="profile-field">
                        <i class="bi bi-phone"></i>
                        <span>${this.escapeHtml(content.mobile_number)}</span>
                        ${content.mobile_verified ? '<i class="bi bi-check-circle-fill verified"></i>' : ''}
                    </div>
                ` : ''}
                ${content.created_at ? `
                    <div class="profile-field">
                        <i class="bi bi-calendar"></i>
                        <span>Member since ${this.formatDate(content.created_at)}</span>
                    </div>
                ` : ''}
                ${content.credentials && content.credentials.length > 0 ? `
                    <div class="profile-field">
                        <i class="bi bi-key"></i>
                        <span>${content.credentials.length} credential${content.credentials.length !== 1 ? 's' : ''}</span>
                    </div>
                ` : ''}
            </div>
        `;
        
        return card;
    }

    /**
     * Render table
     */
    renderTable(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-table';
        
        const content = data.content;
        if (!Array.isArray(content) || content.length === 0) {
            container.textContent = 'No data available';
            return container;
        }
        
        const table = document.createElement('table');
        table.className = 'data-table';
        
        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const columns = Object.keys(content[0]);
        
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = this.formatColumnName(col);
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Body
        const tbody = document.createElement('tbody');
        content.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = row[col] !== null && row[col] !== undefined ? row[col] : '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        container.appendChild(table);
        
        return container;
    }

    /**
     * Render list
     */
    renderList(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-list';
        
        const content = data.content;
        if (!Array.isArray(content)) {
            container.textContent = 'Invalid list data';
            return container;
        }
        
        const ul = document.createElement('ul');
        content.forEach(item => {
            const li = document.createElement('li');
            li.textContent = typeof item === 'object' ? JSON.stringify(item) : item;
            ul.appendChild(li);
        });
        
        container.appendChild(ul);
        return container;
    }

    /**
     * Render execution status
     */
    renderExecutionStatus(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-execution-status';
        
        const status = data.status || 'executing';
        const content = data.content || '';
        
        const animated = metadata && metadata.animated;
        
        container.innerHTML = `
            <div class="execution-status ${status} ${animated ? 'animated' : ''}">
                <div class="status-icon">
                    ${this.getStatusIcon(status)}
                </div>
                <div class="status-content">
                    ${this.escapeHtml(content)}
                </div>
            </div>
        `;
        
        return container;
    }

    /**
     * Render success message
     */
    renderSuccess(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-alert render-success';
        
        const icon = metadata && metadata.icon ? metadata.icon : '✅';
        const content = data.content || '';
        
        container.innerHTML = `
            <span class="alert-icon">${icon}</span>
            <span class="alert-content">${this.escapeHtml(content)}</span>
        `;
        
        return container;
    }

    /**
     * Render error message
     */
    renderError(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-alert render-error';
        
        const content = data.content || '';
        
        container.innerHTML = `
            <span class="alert-icon">❌</span>
            <span class="alert-content">${this.escapeHtml(content)}</span>
        `;
        
        return container;
    }

    /**
     * Render warning message
     */
    renderWarning(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-alert render-warning';
        
        const content = data.content || '';
        
        container.innerHTML = `
            <span class="alert-icon">⚠️</span>
            <span class="alert-content">${this.escapeHtml(content)}</span>
        `;
        
        return container;
    }

    /**
     * Render info message
     */
    renderInfo(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-alert render-info';
        
        const content = data.content || '';
        
        container.innerHTML = `
            <span class="alert-icon">ℹ️</span>
            <span class="alert-content">${this.escapeHtml(content)}</span>
        `;
        
        return container;
    }

    /**
     * Helper: Get status icon
     */
    getStatusIcon(status) {
        const icons = {
            'executing': '⚡',
            'success': '✅',
            'error': '❌',
            'pending': '⏳'
        };
        return icons[status] || '○';
    }

    /**
     * Helper: Format column name
     */
    formatColumnName(name) {
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Helper: Format date
     */
    formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } catch (e) {
            return dateStr;
        }
    }

    /**
     * Helper: Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in other modules
window.MessageRenderer = MessageRenderer;
