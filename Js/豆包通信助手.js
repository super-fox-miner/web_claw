// ==UserScript==
// @name         豆包智能助手   
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  豆包助手，支持WebSocket双向通信、动态配置、纯净悬浮窗
// @author       FoxMiner
// @match        https://www.doubao.com/*
// @match        https://doubao.com/*
// @icon         https://www.doubao.com/favicon.ico
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    const LOG_PREFIX = '🔍 豆包助手';
    const log = {
        info: (...args) => console.log(`%c${LOG_PREFIX} [信息]`, 'color: #3b82f6; font-weight: bold', ...args),
        success: (...args) => console.log(`%c${LOG_PREFIX} [成功]`, 'color: #10b981; font-weight: bold', ...args),
        warn: (...args) => console.warn(`%c${LOG_PREFIX} [警告]`, 'color: #f59e0b; font-weight: bold', ...args),
        error: (...args) => console.error(`%c${LOG_PREFIX} [错误]`, 'color: #ef4444; font-weight: bold', ...args),
        data: (...args) => console.log(`%c${LOG_PREFIX} [数据]`, 'color: #8b5cf6; font-weight: bold', ...args),
        event: (...args) => console.log(`%c${LOG_PREFIX} [事件]`, 'color: #ec4899; font-weight: bold', ...args)
    };

    const state = {
        modes: [],
        selectedMode: null,
        ws: null,
        isSending: false,
        answerObserver: null,
        panelObserver: null,
        reconnectAttempts: 0,
        maxReconnectAttempts: 10
    };

    const API_ENDPOINTS = [
        'http://127.0.0.1:52431',
        'http://localhost:52431',
        'http://127.0.0.1:8080',
        'http://localhost:8080'
    ];
    let currentApiBase = API_ENDPOINTS[0];

    function generateRequestId() {
        return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async function fetchConfig() {
        for (const base of API_ENDPOINTS) {
            try {
                const response = await fetch(`${base}/api/config`);
                log.info(`获取配置：${base}/api/config，状态码：${response.status}`);
                if (response.ok) {
                    const text = await response.text();
                    log.data('配置响应文本:', text.substring(0, 200) + '...');
                    const data = JSON.parse(text);
                    log.data('解析后的数据:', data);
                    if (data.modes && Array.isArray(data.modes)) {
                        state.modes = data.modes;
                        currentApiBase = base;
                        log.success('配置加载成功，模式数量:', state.modes.length);
                        return true;
                    } else {
                        log.error('配置数据格式错误，缺少 modes 数组');
                    }
                }
            } catch (e) {
                log.error(`从 ${base} 加载配置失败:`, e);
            }
        }
        log.error('所有服务器都无法连接，脚本功能将受限');
        state.modes = [];
        return false;
    }

    function connectWebSocket() {
        if (state.ws && state.ws.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const wsUrl = `${currentApiBase.replace('http', 'ws')}/ws`;
            log.info('尝试连接WebSocket:', wsUrl);
            state.ws = new WebSocket(wsUrl);

            state.ws.onopen = () => {
                log.success('WebSocket连接成功');
                state.reconnectAttempts = 0;
                updateServerStatus(true);
            };

            state.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                } catch (e) {
                    log.error('解析WebSocket消息失败:', e);
                }
            };

            state.ws.onclose = () => {
                log.warn('WebSocket连接关闭');
                updateServerStatus(false);
                attemptReconnect();
            };

            state.ws.onerror = (error) => {
                log.error('WebSocket错误:', error);
            };
        } catch (e) {
            log.error('创建WebSocket连接失败:', e);
        }
    }

    function attemptReconnect() {
        if (state.reconnectAttempts >= state.maxReconnectAttempts) {
            log.error('达到最大重连次数，放弃重连');
            return;
        }

        const delay = Math.min(1000 * Math.pow(2, state.reconnectAttempts), 30000);
        state.reconnectAttempts++;
        log.info(`将在 ${delay/1000} 秒后尝试重连 (${state.reconnectAttempts}/${state.maxReconnectAttempts})`);

        setTimeout(() => {
            connectWebSocket();
        }, delay);
    }

    function handleWebSocketMessage(data) {
        log.event('收到WebSocket消息:', data);

        if (data.type === 'result') {
            let output;
            if (data.success) {
                if (typeof data.output === 'object' && data.output !== null) {
                    output = JSON.stringify(data.output);
                } else {
                    output = data.output;
                }
            } else {
                output = `错误: ${data.error}`;
            }
            log.info('收到函数执行结果:', output);
            autoSendResult(output);
        } else if (data.type === 'config_update') {
            state.modes = data.modes;
            log.info('配置已更新');
            refreshPanelButtons();
        }
    }

    function sendExecuteRequest(funcName, params) {
        if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
            log.warn('WebSocket未连接，无法发送请求');
            return;
        }

        const request = {
            type: 'execute',
            id: generateRequestId(),
            function: funcName,
            parameters: params
        };

        state.ws.send(JSON.stringify(request));
        log.info('已发送执行请求:', request);
    }

    function addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .deepseek-helper-panel {
                position: fixed !important;
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                padding: 8px;
                z-index: 999999;
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                min-width: 200px;
                max-width: 500px;
                min-height: 100px;
                backdrop-filter: blur(4px);
                background-color: rgba(255, 255, 255, 0.98);
                font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
                cursor: default;
                transition: box-shadow 0.2s;
                user-select: none;
            }
            .deepseek-helper-panel.dragging {
                opacity: 0.9;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
                transition: none;
            }
            .deepseek-helper-panel .panel-header {
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
                padding-bottom: 4px;
                border-bottom: 1px solid #e5e7eb;
                cursor: move;
                background: #f9fafb;
                margin: -8px -8px 8px -8px;
                padding: 8px;
                border-radius: 12px 12px 0 0;
            }
            .deepseek-helper-panel .panel-title {
                font-size: 12px;
                font-weight: 600;
                color: #4b5563;
                letter-spacing: 0.5px;
            }
            .deepseek-helper-panel .panel-controls {
                display: flex;
                gap: 8px;
            }
            .deepseek-helper-panel .panel-control {
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                background: #e5e7eb;
                color: #4b5563;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
            }
            .deepseek-helper-panel .panel-control:hover {
                background: #3b82f6;
                color: white;
            }
            .deepseek-helper-panel button {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 20px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
                color: #1f2937;
                cursor: pointer;
                transition: all 0.15s ease;
                white-space: nowrap;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                flex: 1 0 auto;
            }
            .deepseek-helper-panel button:hover {
                background: #e5e7eb;
                border-color: #9ca3af;
                transform: translateY(-1px);
            }
            .deepseek-helper-panel button:active {
                transform: translateY(0);
            }
            .deepseek-helper-panel button.active {
                background: #3b82f6;
                border-color: #2563eb;
                color: white;
                box-shadow: 0 2px 4px rgba(59,130,246,0.3);
            }
            .deepseek-helper-panel button.save-true::after {
                content: " 💾";
                font-size: 10px;
            }
            .server-status {
                width: 100%;
                font-size: 10px;
                padding: 2px 4px;
                border-radius: 4px;
                text-align: center;
                margin-top: 4px;
            }
            .server-status.connected {
                background: #10b98120;
                color: #10b981;
            }
            .server-status.disconnected {
                background: #ef444420;
                color: #ef4444;
            }
            .deepseek-helper-note {
                width: 100%;
                font-size: 11px;
                color: #6b7280;
                text-align: center;
                margin-top: 4px;
                border-top: 1px dashed #d1d5db;
                padding-top: 4px;
            }
            .resize-handle {
                position: absolute;
                right: 0;
                bottom: 0;
                width: 12px;
                height: 12px;
                cursor: nwse-resize;
                background: linear-gradient(135deg, transparent 50%, #3b82f6 50%);
                border-bottom-right-radius: 12px;
                z-index: 1;
            }
        `;
        document.head.appendChild(style);
        log.success('CSS样式添加完成');
    }

    let isDragging = false;
    let isResizing = false;
    let currentPanel = null;
    let dragStartX = 0, dragStartY = 0;
    let resizeStartX = 0, resizeStartY = 0;
    let panelStartLeft = 0, panelStartTop = 0;
    let panelStartWidth = 0, panelStartHeight = 0;

    function setupDrag(panel) {
        const header = panel.querySelector('.panel-header');
        header.addEventListener('mousedown', startDrag);
        
        // 创建调整大小手柄
        const resizeHandle = document.createElement('div');
        resizeHandle.className = 'resize-handle';
        panel.appendChild(resizeHandle);
        resizeHandle.addEventListener('mousedown', startResize);
        
        document.addEventListener('mousemove', onDrag);
        document.addEventListener('mousemove', onResize);
        document.addEventListener('mouseup', stopDrag);
        document.addEventListener('mouseup', stopResize);

        function startDrag(e) {
            e.preventDefault();
            isDragging = true;
            isResizing = false;
            currentPanel = panel;

            const rect = panel.getBoundingClientRect();
            panelStartLeft = rect.left;
            panelStartTop = rect.top;
            dragStartX = e.clientX;
            dragStartY = e.clientY;

            panel.classList.add('dragging');
            log.event('开始拖拽面板');
        }

        function onDrag(e) {
            if (!isDragging || !currentPanel) return;
            e.preventDefault();

            const dx = e.clientX - dragStartX;
            const dy = e.clientY - dragStartY;

            let newLeft = panelStartLeft + dx;
            let newTop = panelStartTop + dy;

            newLeft = Math.max(0, Math.min(window.innerWidth - currentPanel.offsetWidth, newLeft));
            newTop = Math.max(0, Math.min(window.innerHeight - currentPanel.offsetHeight, newTop));

            currentPanel.style.left = newLeft + 'px';
            currentPanel.style.top = newTop + 'px';
            currentPanel.style.right = 'auto';
            currentPanel.style.bottom = 'auto';
        }

        function stopDrag() {
            if (isDragging && currentPanel) {
                isDragging = false;
                currentPanel.classList.remove('dragging');
                savePanelSettings(currentPanel);
                log.event('拖拽结束，位置已保存');
            }
        }
        
        function startResize(e) {
            e.preventDefault();
            isResizing = true;
            isDragging = false;
            currentPanel = panel;
            
            const rect = panel.getBoundingClientRect();
            resizeStartX = e.clientX;
            resizeStartY = e.clientY;
            panelStartWidth = rect.width;
            panelStartHeight = rect.height;
            
            panel.classList.add('resizing');
            log.event('开始调整面板大小');
        }
        
        function onResize(e) {
            if (!isResizing || !currentPanel) return;
            e.preventDefault();
            
            const dx = e.clientX - resizeStartX;
            const dy = e.clientY - resizeStartY;
            
            let newWidth = Math.max(200, panelStartWidth + dx);
            let newHeight = Math.max(100, panelStartHeight + dy);
            
            newWidth = Math.min(newWidth, window.innerWidth - parseInt(currentPanel.style.left) - 10);
            newHeight = Math.min(newHeight, window.innerHeight - parseInt(currentPanel.style.top) - 10);
            
            currentPanel.style.width = newWidth + 'px';
            currentPanel.style.height = newHeight + 'px';
        }
        
        function stopResize() {
            if (isResizing && currentPanel) {
                isResizing = false;
                currentPanel.classList.remove('resizing');
                savePanelSettings(currentPanel);
                log.event('调整大小结束，尺寸已保存');
            }
        }
    }

    function loadPanelSettings() {
        try {
            const saved = localStorage.getItem('deepseek_panel_settings');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {
            log.warn('加载面板设置失败:', e);
        }
        return { left: 280, top: 20, width: 300, height: 150 };
    }

    function savePanelSettings(panel) {
        try {
            const settings = {
                left: parseInt(panel.style.left) || 280,
                top: parseInt(panel.style.top) || 20,
                width: parseInt(panel.style.width) || 300,
                height: parseInt(panel.style.height) || 150
            };
            localStorage.setItem('deepseek_panel_settings', JSON.stringify(settings));
        } catch (e) {
            log.warn('保存面板设置失败:', e);
        }
    }

    function createButtonPanel() {
        if (document.getElementById('deepseek-helper-panel')) {
            log.warn('按钮面板已存在，跳过创建');
            return;
        }

        const settings = loadPanelSettings();
        const panel = document.createElement('div');
        panel.className = 'deepseek-helper-panel';
        panel.id = 'deepseek-helper-panel';
        panel.style.left = settings.left + 'px';
        panel.style.top = settings.top + 'px';
        panel.style.width = settings.width + 'px';
        panel.style.height = settings.height + 'px';

        const header = document.createElement('div');
        header.className = 'panel-header';
        header.innerHTML = `
            <span class="panel-title">🤖 豆包助手</span>
            <div class="panel-controls">
                <div class="panel-control" id="panel-minimize">−</div>
                <div class="panel-control" id="panel-reset">↻</div>
            </div>
        `;
        panel.appendChild(header);

        renderPanelButtons(panel);

        const statusDiv = document.createElement('div');
        statusDiv.id = 'server-status';
        statusDiv.className = 'server-status disconnected';
        statusDiv.textContent = '⚡ 检查服务器连接...';
        panel.appendChild(statusDiv);

        const note = document.createElement('div');
        note.className = 'deepseek-helper-note';
        if (state.modes.length === 0) {
            note.textContent = '⚠️ 服务器未连接，功能不可用';
        } else {
            note.textContent = '点击按钮选择模式，回答会自动保存';
        }
        panel.appendChild(note);

        document.body.appendChild(panel);
        setupDrag(panel);

        document.getElementById('panel-minimize')?.addEventListener('click', (e) => {
            e.stopPropagation();
            panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
        });

        document.getElementById('panel-reset')?.addEventListener('click', (e) => {
            e.stopPropagation();
            panel.style.left = '280px';
            panel.style.top = '20px';
            panel.style.width = '300px';
            savePanelSettings(panel);
        });

        log.success('按钮面板创建完成');

        testServerConnection().then(connected => {
            updateServerStatus(connected);
        });
    }

    function renderPanelButtons(panel) {
        const existingButtons = panel.querySelectorAll('button');
        existingButtons.forEach(btn => btn.remove());

        if (state.modes.length === 0) {
            const noServerBtn = document.createElement('button');
            noServerBtn.textContent = '⚠️ 服务器未连接';
            noServerBtn.disabled = true;
            noServerBtn.style.opacity = '0.6';
            panel.insertBefore(noServerBtn, panel.querySelector('#server-status'));
            return;
        }

        state.modes.forEach((cfg, index) => {
            const btn = document.createElement('button');
            btn.textContent = cfg.label;
            if (cfg.save) {
                btn.classList.add('save-true');
            }
            btn.dataset.index = index;

            btn.addEventListener('click', () => {
                log.event(`按钮被点击: ${cfg.label}`);
                panel.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.selectedMode = cfg;
                log.info('当前模式已切换:', state.selectedMode);
            });

            panel.insertBefore(btn, panel.querySelector('#server-status'));
        });

        // 添加删除规则按钮
        const deleteRuleBtn = document.createElement('button');
        deleteRuleBtn.textContent = '删除规则';
        deleteRuleBtn.addEventListener('click', async () => {
            log.event('删除规则按钮被点击');
            await showRuleListForDeletion();
        });
        panel.insertBefore(deleteRuleBtn, panel.querySelector('#server-status'));

        const defaultBtn = panel.querySelector('button');
        if (defaultBtn) {
            defaultBtn.classList.add('active');
            state.selectedMode = state.modes[0];
        }
    }

    function refreshPanelButtons() {
        const panel = document.getElementById('deepseek-helper-panel');
        if (panel) {
            renderPanelButtons(panel);
        }
    }

    async function showRuleListForDeletion() {
        try {
            // 获取规则列表
            const response = await fetch(`${currentApiBase}/api/rules`);
            if (!response.ok) {
                throw new Error(`获取规则列表失败: ${response.status}`);
            }
            const rules = await response.json();
            log.data('获取到的规则列表:', rules);

            if (!rules || rules.length === 0) {
                alert('没有找到规则');
                return;
            }

            // 创建规则选择对话框
            const dialog = document.createElement('div');
            dialog.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                padding: 20px;
                z-index: 999999;
                min-width: 400px;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
            `;

            const title = document.createElement('h3');
            title.textContent = '选择要删除的规则';
            title.style.cssText = 'margin-top: 0; margin-bottom: 16px; font-size: 16px; font-weight: 600;';
            dialog.appendChild(title);

            const ruleList = document.createElement('div');
            ruleList.style.cssText = 'margin-bottom: 16px;';

            rules.forEach(rule => {
                const ruleItem = document.createElement('div');
                ruleItem.style.cssText = `
                    display: flex;
                    align-items: center;
                    padding: 8px 12px;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    margin-bottom: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                `;
                ruleItem.style.backgroundColor = '#f9fafb';

                ruleItem.addEventListener('mouseenter', () => {
                    ruleItem.style.backgroundColor = '#f3f4f6';
                });
                ruleItem.addEventListener('mouseleave', () => {
                    ruleItem.style.backgroundColor = '#f9fafb';
                });

                const ruleInfo = document.createElement('div');
                ruleInfo.style.cssText = 'flex: 1;';
                ruleInfo.innerHTML = `
                    <div style="font-weight: 500; margin-bottom: 2px;">${rule.rule_name || '未命名规则'}</div>
                    <div style="font-size: 12px; color: #6b7280;">ID: ${rule.id}</div>
                `;

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = '删除';
                deleteBtn.style.cssText = `
                    background: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                `;

                deleteBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm(`确定要删除规则 "${rule.rule_name || '未命名规则'}" 吗？`)) {
                        try {
                            const deleteResponse = await fetch(`${currentApiBase}/api/rules/${rule.id}`, {
                                method: 'DELETE'
                            });
                            if (deleteResponse.ok) {
                                alert('规则删除成功');
                                dialog.remove();
                            } else {
                                throw new Error(`删除规则失败: ${deleteResponse.status}`);
                            }
                        } catch (error) {
                            log.error('删除规则失败:', error);
                            alert('删除规则失败，请检查服务器连接');
                        }
                    }
                });

                ruleItem.appendChild(ruleInfo);
                ruleItem.appendChild(deleteBtn);
                ruleList.appendChild(ruleItem);
            });

            dialog.appendChild(ruleList);

            const closeBtn = document.createElement('button');
            closeBtn.textContent = '关闭';
            closeBtn.style.cssText = `
                width: 100%;
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
            `;

            closeBtn.addEventListener('click', () => {
                dialog.remove();
            });

            dialog.appendChild(closeBtn);

            // 创建遮罩层
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999998;
            `;

            overlay.addEventListener('click', () => {
                dialog.remove();
                overlay.remove();
            });

            document.body.appendChild(overlay);
            document.body.appendChild(dialog);
        } catch (error) {
            log.error('获取规则列表失败:', error);
            alert('获取规则列表失败，请检查服务器连接');
        }
    }

    async function testServerConnection() {
        for (const base of API_ENDPOINTS) {
            try {
                const response = await fetch(`${base}/health`);
                if (response.ok) {
                    currentApiBase = base;
                    log.success(`服务器连接成功: ${base}`);
                    return true;
                }
            } catch (e) {
            }
        }
        return false;
    }

    function updateServerStatus(connected) {
        const statusEl = document.getElementById('server-status');
        if (statusEl) {
            statusEl.className = connected ? 'server-status connected' : 'server-status disconnected';
            statusEl.textContent = connected ? '✅ 服务器已连接' : '❌ 服务器未连接';
        }
    }

    // 豆包输入框选择器（请根据实际页面调整）
    function getInputElement() {
        // 豆包常用：textarea 或 contenteditable div
        let input = document.querySelector('textarea[placeholder*="提问" i], textarea[placeholder*="输入" i], div[contenteditable="true"][role="textbox"]');
        if (!input) {
            input = document.querySelector('textarea') || document.querySelector('div[contenteditable="true"]');
        }
        return input;
    }

    // 豆包发送按钮选择器
    function getSendButton() {
        return document.querySelector(
            'button[aria-label="发送"], button[aria-label="Send"], ' +
            'button[class*="send"], button[class*="Send"], ' +
            'button[type="submit"], .send-btn, .chat-send-btn'
        );
    }

    function prependTextToInput() {
        if (!state.selectedMode) return false;
        const inputEl = getInputElement();
        if (!inputEl) return false;

        const prependText = state.selectedMode.text || '';
        let originalText = '';

        if (inputEl.tagName === 'TEXTAREA') {
            originalText = inputEl.value;
        } else if (inputEl.isContentEditable) {
            originalText = inputEl.textContent || inputEl.innerText;
        } else {
            return false;
        }

        let newText = prependText + originalText;

        if (inputEl.tagName === 'TEXTAREA') {
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeSetter.call(inputEl, newText);
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (inputEl.isContentEditable) {
            inputEl.textContent = newText;
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
        }

        return true;
    }

    function sendMessage() {
        if (state.isSending) {
            log.warn('正在发送中，跳过重复触发');
            return;
        }
        state.isSending = true;
        log.event('触发发送消息');

        if (state.selectedMode && state.selectedMode.text !== '') {
            const inserted = prependTextToInput();
            if (!inserted) {
                state.isSending = false;
                return;
            }
        }

        setTimeout(() => {
            const sendButton = getSendButton();
            if (sendButton && !sendButton.disabled) {
                sendButton.click();
                log.success('发送按钮已点击');
            } else {
                const inputEl = getInputElement();
                if (inputEl) {
                    const enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    });
                    inputEl.dispatchEvent(enterEvent);
                }
            }

            setTimeout(() => { state.isSending = false; }, 200);
        }, 100);
    }

    function autoSendResult(result) {
        if (state.isSending) {
            log.warn('正在发送中，跳过自动发送');
            return;
        }

        log.event('自动发送结果:', result);
        const inputEl = getInputElement();
        if (!inputEl) {
            log.warn('未找到输入框');
            return;
        }

        state.isSending = true;

        if (inputEl.tagName === 'TEXTAREA') {
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeSetter.call(inputEl, result);
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (inputEl.isContentEditable) {
            inputEl.textContent = result;
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
        }

        setTimeout(() => {
            const sendButton = getSendButton();
            if (sendButton && !sendButton.disabled) {
                sendButton.click();
                log.success('结果已自动发送（点击发送按钮）');
            } else {
                log.warn('未找到可用的发送按钮，尝试模拟回车');
                if (inputEl) {
                    const enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    });
                    inputEl.dispatchEvent(enterEvent);
                    log.success('结果已自动发送（模拟回车）');
                }
            }

            setTimeout(() => { state.isSending = false; }, 200);
        }, 500);
    }

    // 获取豆包最后一条 AI 回答（请根据实际 DOM 结构调整）
    function getLastAssistantMessage() {
    // 豆包最新消息的选择器：根据实际DOM调整
    const selectors = [
        '[data-testid="message_text_content"]',      // 您提供的结构中的关键属性
        '.message-item.assistant',
        '.assistant-message',
        '.chat-message-assistant',
        '[data-role="assistant"]'
    ];

    for (const sel of selectors) {
        const elements = document.querySelectorAll(sel);
        if (elements.length > 0) {
            // 取最后一个消息元素
            const lastMsg = elements[elements.length - 1];
            // 获取纯文本（会包含代码块内容）
            const message = lastMsg.innerText || lastMsg.textContent || '';
            if (message.trim()) {
                console.log(`[调试] 获取到消息：`, message.substring(0, 200) + '...');
                return message;
            }
        }
    }
    return '';
}

    let lastSavedAnswerHash = '';
    let lastAnswerLength = 0;
    const DEBOUNCE_DELAY = 800;
    let saveDebounceTimer = null;

    function debouncedSave() {
        if (!state.selectedMode?.save) {
            return;
        }

        if (saveDebounceTimer) clearTimeout(saveDebounceTimer);

        saveDebounceTimer = setTimeout(() => {
            const answerText = getLastAssistantMessage();
            if (answerText) {
                // 检查是否包含“发送任务至服务器”文本（可根据实际需要调整关键词）
                if (answerText.includes('发送任务至服务器')) {
                    log.info('检测到“发送任务至服务器”文本，准备处理');
                    checkAndExecuteFunctionCall(answerText);
                }
            }
        }, DEBOUNCE_DELAY);
    }

    function checkAndExecuteFunctionCall(content) {
        log.event('检查function call...');

        // 检测是否被JSON代码块包裹
        const isJsonCodeBlock = /^\s*```json[\s\S]*```\s*$/.test(content);
        log.data('是否被JSON代码块包裹:', isJsonCodeBlock);

        // 方法1: 尝试提取并解析JSON代码块
        try {
            let jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/);
            if (jsonMatch) {
                const functionCall = JSON.parse(jsonMatch[1].trim());
                log.data('从代码块解析到function call:', functionCall);
                sendExecuteRequest(functionCall.function, functionCall.parameters);
                return;
            }
        } catch (e) {
            log.warn('代码块解析失败:', e.message);
        }

        // 方法2: 尝试直接解析整个内容
        try {
            const functionCall = JSON.parse(content.trim());
            log.data('直接解析到function call:', functionCall);
            sendExecuteRequest(functionCall.function, functionCall.parameters);
            return;
        } catch (e) {
            log.warn('直接解析失败:', e.message);
        }

        // 方法3: 尝试提取纯JSON对象（忽略前后的文本）
        try {
            const jsonStart = content.indexOf('{');
            if (jsonStart !== -1) {
                let jsonStr = content.substring(jsonStart);
                let braceCount = 1;
                let jsonEnd = jsonStart + 1;
                while (braceCount > 0 && jsonEnd < content.length) {
                    if (content[jsonEnd] === '{') braceCount++;
                    if (content[jsonEnd] === '}') braceCount--;
                    jsonEnd++;
                }
                jsonStr = content.substring(jsonStart, jsonEnd);
                const functionCall = JSON.parse(jsonStr);
                log.data('从纯JSON对象解析到function call:', functionCall);
                sendExecuteRequest(functionCall.function, functionCall.parameters);
                return;
            }
        } catch (e) {
            log.warn('纯JSON对象解析失败:', e.message);
        }

        // 方法4: 匹配JSON对象格式
        try {
            let jsonMatch = content.match(/\{[\s\S]*?\}/);
            if (jsonMatch) {
                const functionCall = JSON.parse(jsonMatch[0].trim());
                log.data('从对象解析到function call:', functionCall);
                sendExecuteRequest(functionCall.function, functionCall.parameters);
                return;
            }
        } catch (e) {
            log.warn('对象解析失败:', e.message);
        }

        // 方法5: 使用更宽松的解析方式
        try {
            let jsonStr = content.replace(/^[\s\S]*?\{/, '{').replace(/```json\s*/g, '').replace(/```/g, '').trim();
            jsonStr = jsonStr
                .replace(/("[^"]*)(\n)([^"]*")/g, '$1\\n$3')
                .replace(/(?<!\\)"(?![\s,:\]\}])/g, '\\"')
                .replace(/\n/g, '\\n')
                .replace(/\r/g, '\\r');

            const functionCall = JSON.parse(jsonStr);
            log.data('宽松解析到function call:', functionCall);
            sendExecuteRequest(functionCall.function, functionCall.parameters);
            return;
        } catch (e) {
            log.warn('宽松解析失败:', e.message);
        }

        // 方法6: 使用eval（谨慎使用，仅作为最后手段）
        try {
            const jsonStart = content.indexOf('{');
            if (jsonStart !== -1) {
                let braceCount = 1;
                let jsonEnd = jsonStart + 1;
                while (braceCount > 0 && jsonEnd < content.length) {
                    if (content[jsonEnd] === '{') braceCount++;
                    if (content[jsonEnd] === '}') braceCount--;
                    jsonEnd++;
                }
                const jsonStr = content.substring(jsonStart, jsonEnd);
                const functionCall = (0, eval)(`(${jsonStr})`);
                if (functionCall && functionCall.function && functionCall.parameters) {
                    log.data('使用eval解析到function call:', functionCall);
                    sendExecuteRequest(functionCall.function, functionCall.parameters);
                    return;
                }
            }
        } catch (e) {
            log.warn('eval解析失败:', e.message);
        }

        log.error('所有解析方法都失败，无法识别function call');
        log.error('原始内容:', content);
    }

    function setupAnswerObserver() {
        log.event('设置回答监听器');

        if (state.answerObserver) state.answerObserver.disconnect();

        // 豆包消息容器可能为以下选择器之一，请根据实际调整
        const container = document.querySelector('.chat-messages, .message-list, main') || document.body;

        state.answerObserver = new MutationObserver(() => {
            debouncedSave();
        });

        state.answerObserver.observe(container, {
            childList: true,
            subtree: true,
            characterData: true
        });

        log.success('回答监听器设置完成，监听容器:', container);
    }

    function setupSendInterceptors() {
        log.event('设置发送事件拦截器');

        document.addEventListener('click', function(e) {
            if (state.isSending) return;

            const sendButton = e.target.closest(
                'button[aria-label="发送"], button[aria-label="Send"], ' +
                'button[class*="send"], button[class*="Send"], ' +
                'button[type="submit"]'
            );

            if (sendButton && state.selectedMode && state.selectedMode.text !== '') {
                log.event('检测到发送按钮点击');
                e.preventDefault();
                e.stopPropagation();
                sendMessage();
            }
        }, true);

        document.addEventListener('keydown', function(e) {
            if (state.isSending) return;

            if (e.key === 'Enter' && !e.shiftKey) {
                const inputEl = e.target.closest('textarea, div[contenteditable="true"]');
                const inputField = getInputElement();

                if (inputEl && inputField && (inputEl === inputField || inputField.contains(inputEl))) {
                    if (!state.selectedMode || state.selectedMode.text === '') {
                        log.event('“无”模式，不拦截回车，由页面处理');
                        return;
                    }

                    log.event('检测到回车键，准备插入文本并发送');
                    e.preventDefault();
                    e.stopPropagation();
                    sendMessage();
                }
            }
        }, true);
    }

    function watchPanelRemoval() {
        if (state.panelObserver) state.panelObserver.disconnect();

        state.panelObserver = new MutationObserver((mutations) => {
            for (const mut of mutations) {
                if (mut.removedNodes.length > 0) {
                    for (const node of mut.removedNodes) {
                        if (node.id === 'deepseek-helper-panel') {
                            log.warn('面板被移除，重新创建');
                            createButtonPanel();
                            break;
                        }
                    }
                }
            }
        });

        state.panelObserver.observe(document.body, { childList: true, subtree: false });
    }

    async function init() {
        log.info('='.repeat(50));
        log.info('开始初始化豆包助手 (双向通信版)');
        log.info('='.repeat(50));

        await fetchConfig();
        addStyles();
        createButtonPanel();
        setupSendInterceptors();
        setupAnswerObserver();
        watchPanelRemoval();
        connectWebSocket();

        log.success('初始化完成');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();