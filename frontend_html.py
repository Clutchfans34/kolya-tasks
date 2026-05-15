HTML_CONTENT = """<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Коля — Task Manager</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg: #0D1B2A;
      --bg2: #1A2744;
      --bg3: #1e3a5f;
      --accent: #3B82F6;
      --accent2: #60A5FA;
      --green: #10B981;
      --yellow: #F59E0B;
      --red: #EF4444;
      --text: #F1F5F9;
      --text2: #94A3B8;
      --border: rgba(255,255,255,0.08);
      --radius: 16px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* HEADER */
    .header {
      background: var(--bg2);
      padding: 16px 20px 12px;
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-top {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .avatar {
      width: 40px; height: 40px;
      background: linear-gradient(135deg, var(--accent), #7C3AED);
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; font-weight: 700;
      flex-shrink: 0;
    }
    .header-title { font-size: 18px; font-weight: 700; }
    .header-sub { font-size: 12px; color: var(--text2); }

    /* TABS */
    .tabs {
      display: flex;
      gap: 4px;
      background: var(--bg);
      border-radius: 12px;
      padding: 4px;
    }
    .tab {
      flex: 1;
      padding: 8px 4px;
      text-align: center;
      font-size: 12px;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      color: var(--text2);
      transition: all 0.2s;
      border: none;
      background: none;
    }
    .tab.active {
      background: var(--accent);
      color: white;
    }

    /* PAGES */
    .page { display: none; padding: 16px; }
    .page.active { display: block; }

    /* STATS CARDS */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: var(--bg2);
      border-radius: var(--radius);
      padding: 14px 10px;
      text-align: center;
      border: 1px solid var(--border);
    }
    .stat-number {
      font-size: 28px;
      font-weight: 800;
      line-height: 1;
      margin-bottom: 4px;
    }
    .stat-label { font-size: 11px; color: var(--text2); font-weight: 500; }
    .stat-card.todo .stat-number { color: var(--accent2); }
    .stat-card.inprogress .stat-number { color: var(--yellow); }
    .stat-card.done .stat-number { color: var(--green); }

    /* SECTION TITLE */
    .section-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--text2);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 10px;
    }

    /* TASK CARD */
    .task-card {
      background: var(--bg2);
      border-radius: var(--radius);
      padding: 14px 16px;
      margin-bottom: 10px;
      border: 1px solid var(--border);
      display: flex;
      gap: 12px;
      align-items: flex-start;
      transition: opacity 0.2s;
    }
    .task-card.done-card { opacity: 0.5; }
    .priority-dot {
      width: 10px; height: 10px;
      border-radius: 50%;
      margin-top: 5px;
      flex-shrink: 0;
    }
    .priority-high { background: var(--red); box-shadow: 0 0 6px var(--red); }
    .priority-medium { background: var(--yellow); box-shadow: 0 0 6px var(--yellow); }
    .priority-low { background: var(--green); box-shadow: 0 0 6px var(--green); }
    .task-body { flex: 1; min-width: 0; }
    .task-title {
      font-size: 15px;
      font-weight: 600;
      line-height: 1.3;
      margin-bottom: 4px;
    }
    .task-title.striked { text-decoration: line-through; color: var(--text2); }
    .task-meta {
      font-size: 12px;
      color: var(--text2);
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }
    .task-due { color: var(--yellow); }
    .task-due.overdue { color: var(--red); }
    .task-actions {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex-shrink: 0;
    }
    .btn-icon {
      width: 32px; height: 32px;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      font-size: 15px;
      transition: all 0.2s;
    }
    .btn-done { background: rgba(16,185,129,0.15); }
    .btn-done:hover { background: rgba(16,185,129,0.3); }
    .btn-delete { background: rgba(239,68,68,0.15); }
    .btn-delete:hover { background: rgba(239,68,68,0.3); }
    .btn-inprogress { background: rgba(245,158,11,0.15); }

    /* EMPTY STATE */
    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: var(--text2);
    }
    .empty-state .icon { font-size: 48px; margin-bottom: 12px; }
    .empty-state p { font-size: 15px; }

    /* FILTER TABS */
    .filter-tabs {
      display: flex;
      gap: 6px;
      margin-bottom: 16px;
      overflow-x: auto;
      padding-bottom: 4px;
    }
    .filter-tab {
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      border: 1px solid var(--border);
      background: none;
      color: var(--text2);
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }
    .filter-tab.active {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
    }

    /* ADD BUTTON */
    .fab {
      position: fixed;
      bottom: 80px;
      right: 20px;
      width: 56px; height: 56px;
      background: var(--accent);
      border-radius: 50%;
      border: none;
      color: white;
      font-size: 26px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 20px rgba(59,130,246,0.5);
      z-index: 50;
      transition: transform 0.2s;
    }
    .fab:active { transform: scale(0.9); }

    /* MODAL */
    .modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.7);
      z-index: 200;
      display: none;
      align-items: flex-end;
    }
    .modal-overlay.open { display: flex; }
    .modal {
      background: var(--bg2);
      border-radius: 24px 24px 0 0;
      padding: 24px 20px 40px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
    }
    .modal-title {
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 20px;
    }
    .form-group { margin-bottom: 16px; }
    .form-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text2);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
      display: block;
    }
    .form-input {
      width: 100%;
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 16px;
      color: var(--text);
      font-size: 15px;
      outline: none;
      font-family: inherit;
    }
    .form-input:focus { border-color: var(--accent); }
    .priority-select {
      display: flex;
      gap: 8px;
    }
    .priority-btn {
      flex: 1;
      padding: 10px;
      border-radius: 10px;
      border: 2px solid var(--border);
      background: none;
      color: var(--text2);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      text-align: center;
    }
    .priority-btn[data-p="high"].active { border-color: var(--red); color: var(--red); background: rgba(239,68,68,0.1); }
    .priority-btn[data-p="medium"].active { border-color: var(--yellow); color: var(--yellow); background: rgba(245,158,11,0.1); }
    .priority-btn[data-p="low"].active { border-color: var(--green); color: var(--green); background: rgba(16,185,129,0.1); }
    .btn-primary {
      width: 100%;
      padding: 16px;
      background: var(--accent);
      border: none;
      border-radius: 14px;
      color: white;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      margin-top: 8px;
      transition: opacity 0.2s;
    }
    .btn-primary:active { opacity: 0.8; }
    .btn-cancel {
      width: 100%;
      padding: 14px;
      background: none;
      border: 1px solid var(--border);
      border-radius: 14px;
      color: var(--text2);
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 8px;
    }

    /* CHAT PAGE */
    .chat-messages {
      padding: 16px;
      padding-bottom: 100px;
      min-height: calc(100vh - 130px);
    }
    .chat-bubble {
      max-width: 85%;
      margin-bottom: 12px;
      padding: 12px 16px;
      border-radius: 18px;
      font-size: 15px;
      line-height: 1.5;
      white-space: pre-wrap;
    }
    .bubble-kolya {
      background: var(--bg2);
      border-bottom-left-radius: 4px;
      margin-right: auto;
      border: 1px solid var(--border);
    }
    .bubble-user {
      background: var(--accent);
      border-bottom-right-radius: 4px;
      margin-left: auto;
    }
    .bubble-time {
      font-size: 11px;
      color: var(--text2);
      margin-top: 4px;
      padding: 0 4px;
    }
    .bubble-time.right { text-align: right; }
    .typing-indicator {
      display: flex;
      gap: 4px;
      padding: 12px 16px;
      background: var(--bg2);
      border-radius: 18px;
      border-bottom-left-radius: 4px;
      width: fit-content;
      margin-bottom: 12px;
      border: 1px solid var(--border);
    }
    .dot {
      width: 8px; height: 8px;
      background: var(--text2);
      border-radius: 50%;
      animation: bounce 1.2s infinite;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-6px); }
    }

    /* CHAT INPUT */
    .chat-input-bar {
      position: fixed;
      bottom: 0;
      left: 0; right: 0;
      background: var(--bg2);
      border-top: 1px solid var(--border);
      padding: 10px 16px 16px;
      display: flex;
      gap: 10px;
      align-items: flex-end;
      z-index: 100;
    }
    .chat-input {
      flex: 1;
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 10px 16px;
      color: var(--text);
      font-size: 15px;
      outline: none;
      font-family: inherit;
      resize: none;
      min-height: 44px;
      max-height: 120px;
    }
    .chat-input:focus { border-color: var(--accent); }
    .send-btn {
      width: 44px; height: 44px;
      background: var(--accent);
      border: none;
      border-radius: 50%;
      color: white;
      font-size: 18px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
      transition: transform 0.2s;
    }
    .send-btn:active { transform: scale(0.9); }

    /* TASK CREATED NOTIFICATION */
    .task-created-notif {
      background: rgba(16,185,129,0.15);
      border: 1px solid var(--green);
      border-radius: 12px;
      padding: 10px 14px;
      margin: 8px 0;
      font-size: 13px;
      color: var(--green);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* PROGRESS BAR */
    .progress-section {
      background: var(--bg2);
      border-radius: var(--radius);
      padding: 16px;
      margin-bottom: 16px;
      border: 1px solid var(--border);
    }
    .progress-title {
      font-size: 13px;
      color: var(--text2);
      margin-bottom: 10px;
      font-weight: 600;
    }
    .progress-bar-wrap {
      background: rgba(255,255,255,0.08);
      border-radius: 8px;
      height: 8px;
      overflow: hidden;
      margin-bottom: 6px;
    }
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--green));
      border-radius: 8px;
      transition: width 0.5s ease;
    }
    .progress-pct { font-size: 13px; font-weight: 700; color: var(--green); }

    /* LOADER */
    .loader {
      display: flex;
      justify-content: center;
      padding: 30px;
    }
    .spinner {
      width: 32px; height: 32px;
      border: 3px solid var(--border);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* SCROLLBAR */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
  </style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div class="header-top">
    <div class="avatar">К</div>
    <div>
      <div class="header-title">Коля</div>
      <div class="header-sub">Персональний AI-асистент</div>
    </div>
  </div>
  <div class="tabs">
    <button class="tab active" onclick="showPage('tasks')">📋 Задачі</button>
    <button class="tab" onclick="showPage('chat')">💬 Коля</button>
    <button class="tab" onclick="showPage('stats')">📊 Аналіз</button>
  </div>
</div>

<!-- PAGE: TASKS -->
<div class="page active" id="page-tasks">
  <div style="margin-top: 16px;">
    <div class="filter-tabs">
      <button class="filter-tab active" data-filter="all" onclick="setFilter('all', this)">Всі</button>
      <button class="filter-tab" data-filter="todo" onclick="setFilter('todo', this)">Заплановані</button>
      <button class="filter-tab" data-filter="in_progress" onclick="setFilter('in_progress', this)">В роботі</button>
      <button class="filter-tab" data-filter="done" onclick="setFilter('done', this)">Виконані</button>
    </div>
    <div id="tasks-list">
      <div class="empty-state"><div class="icon">⏳</div><p>Завантаження...</p></div>
    </div>
  </div>
</div>

<!-- PAGE: CHAT -->
<div class="page" id="page-chat">
  <div class="chat-messages" id="chat-messages">
    <div class="chat-bubble bubble-kolya">
      Привіт! Я Коля 👋<br><br>
      Просто напиши мені задачу — наприклад:<br>
      <em>"Зустрітись з Максимом у п'ятницю о 15:00"</em><br><br>
      Або запитай: <em>"Що в мене на сьогодні?"</em>
    </div>
  </div>
  <div class="chat-input-bar">
    <textarea class="chat-input" id="chat-input" placeholder="Напиши задачу або запитай Колю..." rows="1"
      onkeydown="handleChatKey(event)" oninput="autoResize(this)"></textarea>
    <button class="send-btn" onclick="sendMessage()">➤</button>
  </div>
</div>

<!-- PAGE: STATS -->
<div class="page" id="page-stats">
  <div style="margin-top: 16px;" id="stats-content">
    <div class="loader"><div class="spinner"></div></div>
  </div>
</div>

<!-- FAB -->
<button class="fab" id="fab-btn" onclick="openModal()">+</button>

<!-- ADD TASK MODAL -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
  <div class="modal">
    <div class="modal-title">➕ Нова задача</div>

    <div class="form-group">
      <label class="form-label">Назва задачі</label>
      <input type="text" class="form-input" id="task-title" placeholder="Що потрібно зробити?">
    </div>

    <div class="form-group">
      <label class="form-label">Деталі (опційно)</label>
      <textarea class="form-input" id="task-desc" placeholder="Додаткова інформація..." rows="2"></textarea>
    </div>

    <div class="form-group">
      <label class="form-label">Пріоритет</label>
      <div class="priority-select">
        <button class="priority-btn" data-p="high" onclick="selectPriority('high')">🔴 Високий</button>
        <button class="priority-btn active" data-p="medium" onclick="selectPriority('medium')">🟡 Середній</button>
        <button class="priority-btn" data-p="low" onclick="selectPriority('low')">🟢 Низький</button>
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Дедлайн (опційно)</label>
      <input type="date" class="form-input" id="task-due">
    </div>

    <button class="btn-primary" onclick="submitTask()">Створити задачу</button>
    <button class="btn-cancel" onclick="closeModal()">Скасувати</button>
  </div>
</div>

<script>
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const API = 'https://kolya-tasks-production.up.railway.app';
let userId = 0;
let currentFilter = 'all';
let selectedPriority = 'medium';
let allTasks = [];

// Get user_id: спочатку з Telegram WebApp, потім з URL
if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
  userId = tg.initDataUnsafe.user.id;
} else {
  const params = new URLSearchParams(window.location.search);
  userId = parseInt(params.get('user_id')) || 12345;
}

// Init — не чекаємо DOMContentLoaded, запускаємо одразу
function init() {
  loadTasks();
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// PAGE SWITCHING
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  event.target.classList.add('active');

  const fab = document.getElementById('fab-btn');
  fab.style.display = name === 'tasks' ? 'flex' : 'none';

  if (name === 'stats') loadStats();
  if (name === 'tasks') loadTasks();
}

// TASKS
async function loadTasks() {
  const container = document.getElementById('tasks-list');
  try {
    const res = await fetch(`${API}/api/tasks?user_id=${userId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    allTasks = data.tasks || [];
  } catch(e) {
    allTasks = [];
    container.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><p>Помилка завантаження.<br>ID: ${userId}<br>${e.message}</p></div>`;
    return;
  }
  renderTasks();
}

function setFilter(filter, el) {
  currentFilter = filter;
  document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  renderTasks();
}

function renderTasks() {
  const container = document.getElementById('tasks-list');
  let tasks = allTasks;

  if (currentFilter !== 'all') {
    tasks = tasks.filter(t => t.status === currentFilter);
  }

  if (tasks.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="icon">${currentFilter === 'done' ? '🎉' : '📭'}</div>
        <p>${currentFilter === 'done' ? 'Немає виконаних задач' : 'Немає задач.<br>Натисни + або напиши Колі!'}</p>
      </div>`;
    return;
  }

  const today = new Date().toISOString().split('T')[0];

  container.innerHTML = tasks.map(t => {
    const isDone = t.status === 'done';
    const isOverdue = t.due_date && t.due_date < today && !isDone;
    const priorityClass = `priority-${t.priority}`;

    let dueHtml = '';
    if (t.due_date) {
      const cls = isOverdue ? 'task-due overdue' : 'task-due';
      const label = isOverdue ? '⚠️ ' + t.due_date : '📅 ' + t.due_date;
      dueHtml = `<span class="${cls}">${label}</span>`;
    }

    const statusBadge = t.status === 'in_progress' ? '<span style="color:var(--yellow)">⏳ В роботі</span>' : '';

    return `
    <div class="task-card ${isDone ? 'done-card' : ''}" id="task-${t.id}">
      <div class="priority-dot ${priorityClass}"></div>
      <div class="task-body">
        <div class="task-title ${isDone ? 'striked' : ''}">${escapeHtml(t.title)}</div>
        <div class="task-meta">
          ${dueHtml}
          ${statusBadge}
        </div>
      </div>
      <div class="task-actions">
        ${!isDone ? `<button class="btn-icon btn-done" onclick="markDone(${t.id})" title="Виконано">✅</button>` : ''}
        ${t.status === 'todo' ? `<button class="btn-icon btn-inprogress" onclick="markInProgress(${t.id})" title="В роботі">⏳</button>` : ''}
        <button class="btn-icon btn-delete" onclick="deleteTask(${t.id})" title="Видалити">🗑</button>
      </div>
    </div>`;
  }).join('');
}

async function markDone(id) {
  await fetch(`${API}/api/tasks/${id}`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: userId, status: 'done'})
  });
  const task = allTasks.find(t => t.id === id);
  if (task) task.status = 'done';
  renderTasks();
  if (tg) tg.HapticFeedback?.notificationOccurred('success');
}

async function markInProgress(id) {
  await fetch(`${API}/api/tasks/${id}`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: userId, status: 'in_progress'})
  });
  const task = allTasks.find(t => t.id === id);
  if (task) task.status = 'in_progress';
  renderTasks();
}

async function deleteTask(id) {
  if (!confirm('Видалити задачу?')) return;
  await fetch(`${API}/api/tasks/${id}?user_id=${userId}`, {method: 'DELETE'});
  allTasks = allTasks.filter(t => t.id !== id);
  renderTasks();
  if (tg) tg.HapticFeedback?.notificationOccurred('warning');
}

// MODAL
function openModal() {
  document.getElementById('modal-overlay').classList.add('open');
  document.getElementById('task-title').focus();
  if (tg) tg.HapticFeedback?.impactOccurred('light');
}

function closeModal(e) {
  if (!e || e.target === document.getElementById('modal-overlay')) {
    document.getElementById('modal-overlay').classList.remove('open');
    document.getElementById('task-title').value = '';
    document.getElementById('task-desc').value = '';
    document.getElementById('task-due').value = '';
    selectPriority('medium');
  }
}

function selectPriority(p) {
  selectedPriority = p;
  document.querySelectorAll('.priority-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.priority-btn[data-p="${p}"]`).classList.add('active');
}

async function submitTask() {
  const title = document.getElementById('task-title').value.trim();
  if (!title) {
    document.getElementById('task-title').focus();
    return;
  }
  const desc = document.getElementById('task-desc').value.trim();
  const due = document.getElementById('task-due').value || null;

  const res = await fetch(`${API}/api/tasks`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: userId, title, description: desc, priority: selectedPriority, due_date: due})
  });
  const data = await res.json();

  allTasks.unshift({
    id: data.id, title, description: desc,
    priority: selectedPriority, status: 'todo',
    due_date: due, created_at: new Date().toISOString()
  });

  closeModal();
  renderTasks();
  if (tg) tg.HapticFeedback?.notificationOccurred('success');
}

// CHAT
let chatMessages = [];

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;

  input.value = '';
  input.style.height = 'auto';

  appendBubble(msg, 'user');

  const typing = showTyping();

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: userId, message: msg})
    });
    const data = await res.json();

    typing.remove();
    appendBubble(data.text, 'kolya');

    if (data.task_created) {
      const notif = document.createElement('div');
      notif.className = 'task-created-notif';
      notif.innerHTML = `✅ Задача додана: <strong>${escapeHtml(data.task_created.title)}</strong>`;
      document.getElementById('chat-messages').appendChild(notif);
      allTasks.unshift({...data.task_created, status: 'todo', description: ''});
    }

  } catch(e) {
    typing.remove();
    appendBubble('Помилка зв\'язку. Спробуй ще раз.', 'kolya');
  }

  scrollChat();
}

function appendBubble(text, who) {
  const container = document.getElementById('chat-messages');
  const wrap = document.createElement('div');

  const now = new Date().toLocaleTimeString('uk', {hour: '2-digit', minute: '2-digit'});
  const isUser = who === 'user';

  wrap.innerHTML = `
    <div class="chat-bubble ${isUser ? 'bubble-user' : 'bubble-kolya'}">${escapeHtml(text)}</div>
    <div class="bubble-time ${isUser ? 'right' : ''}">${now}</div>
  `;
  container.appendChild(wrap);
  scrollChat();
}

function showTyping() {
  const container = document.getElementById('chat-messages');
  const el = document.createElement('div');
  el.className = 'typing-indicator';
  el.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
  container.appendChild(el);
  scrollChat();
  return el;
}

function scrollChat() {
  const container = document.getElementById('chat-messages');
  container.scrollTop = container.scrollHeight;
}

// STATS
async function loadStats() {
  const container = document.getElementById('stats-content');
  const res = await fetch(`${API}/api/stats?user_id=${userId}`);
  const stats = await res.json();

  const total = (stats.todo || 0) + (stats.in_progress || 0) + (stats.done || 0);
  const done = stats.done || 0;
  const pct = total > 0 ? Math.round(done / total * 100) : 0;

  container.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card todo">
        <div class="stat-number">${stats.todo || 0}</div>
        <div class="stat-label">📋 План</div>
      </div>
      <div class="stat-card inprogress">
        <div class="stat-number">${stats.in_progress || 0}</div>
        <div class="stat-label">⏳ В роботі</div>
      </div>
      <div class="stat-card done">
        <div class="stat-number">${stats.done || 0}</div>
        <div class="stat-label">✅ Готово</div>
      </div>
    </div>

    <div class="progress-section">
      <div class="progress-title">Загальний прогрес</div>
      <div class="progress-bar-wrap">
        <div class="progress-bar-fill" style="width: ${pct}%"></div>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:12px; color:var(--text2)">${done} з ${total} задач</span>
        <span class="progress-pct">${pct}%</span>
      </div>
    </div>

    <div class="section-title">Розподіл по пріоритетах</div>
    ${renderPriorityStats()}
  `;
}

function renderPriorityStats() {
  const high = allTasks.filter(t => t.priority === 'high').length;
  const medium = allTasks.filter(t => t.priority === 'medium').length;
  const low = allTasks.filter(t => t.priority === 'low').length;

  return `
    <div style="display:flex; flex-direction:column; gap:10px; margin-top:10px;">
      <div style="background:var(--bg2); border-radius:12px; padding:14px; border:1px solid var(--border); display:flex; justify-content:space-between;">
        <span>🔴 Високий</span> <strong>${high}</strong>
      </div>
      <div style="background:var(--bg2); border-radius:12px; padding:14px; border:1px solid var(--border); display:flex; justify-content:space-between;">
        <span>🟡 Середній</span> <strong>${medium}</strong>
      </div>
      <div style="background:var(--bg2); border-radius:12px; padding:14px; border:1px solid var(--border); display:flex; justify-content:space-between;">
        <span>🟢 Низький</span> <strong>${low}</strong>
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\n/g, '<br>');
}
</script>
</body>
</html>
"""