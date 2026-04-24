// ==UserScript==
// @name         Gemini Business Import JSON Helper
// @namespace    https://github.com/yukkcat/gemini-business2api
// @version      2.2.0
// @description  Copy import-ready gemini-business2api account JSON. Shift+Click downloads a file.
// @match        https://business.gemini.google/*
// @grant        GM_addStyle
// @grant        GM_cookie
// @grant        GM_setClipboard
// @downloadURL  https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/tools/tampermonkey/gemini-business-import.user.js
// @updateURL    https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/tools/tampermonkey/gemini-business-import.user.js
// @homepageURL  https://github.com/yukkcat/gemini-business2api
// ==/UserScript==

(function () {
  'use strict';

  const BUTTON_ID = 'gb-btn';
  const DEFAULT_LABEL = 'Copy JSON';
  const COPY_LABEL = 'Copied';
  const DOWNLOAD_LABEL = 'Saved';
  const ERROR_LABEL = 'Error';
  const SETUP_LABEL = 'Setup';
  const DEFAULT_TITLE = 'Copy import-ready JSON (expires in 12h). Shift+Click downloads a file.';
  const SETUP_TITLE = '需要先开启 Tampermonkey Cookie 权限';
  const ACCOUNT_EXPIRE_HOURS = 12;
  const SETUP_GUIDE = [
    '脚本需要 Cookie 权限后才能读取账号信息。',
    '1. Tampermonkey -> 通用 -> 配置模式：高级',
    '2. Tampermonkey -> 安全 -> 允许脚本访问 Cookie：All',
    '3. 如果仍然没有权限，请在浏览器扩展页开启开发者模式',
    '4. 修改后刷新 business.gemini.google 页面再重试',
  ];

  GM_addStyle(`
    #${BUTTON_ID} {
      position: fixed;
      right: 32px;
      bottom: 32px;
      min-width: 86px;
      height: 44px;
      padding: 0 14px;
      border: none;
      border-radius: 999px;
      background: linear-gradient(135deg, #1a73e8, #1557b0);
      box-shadow: 0 10px 26px rgba(26, 115, 232, 0.28);
      cursor: pointer;
      z-index: 9999;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.02em;
      transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
      user-select: none;
    }

    #${BUTTON_ID}:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 30px rgba(26, 115, 232, 0.32);
    }

    #${BUTTON_ID}:active {
      transform: translateY(0);
    }
  `);

  const button = document.createElement('button');
  button.id = BUTTON_ID;
  button.type = 'button';
  button.textContent = DEFAULT_LABEL;
  button.title = DEFAULT_TITLE;
  document.body.appendChild(button);

  let resetTimer = null;

  const setButtonState = (label, background, title = DEFAULT_TITLE) => {
    button.textContent = label;
    button.title = title;
    button.style.background = background;
  };

  const flashButtonState = (label, background, title = DEFAULT_TITLE) => {
    if (resetTimer) {
      clearTimeout(resetTimer);
      resetTimer = null;
    }

    setButtonState(label, background, title);
    resetTimer = window.setTimeout(() => {
      setButtonState(DEFAULT_LABEL, 'linear-gradient(135deg, #1a73e8, #1557b0)', DEFAULT_TITLE);
      resetTimer = null;
    }, 1600);
  };

  const buildExpireAt = () => {
    const date = new Date(Date.now() + ACCOUNT_EXPIRE_HOURS * 60 * 60 * 1000);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
  };

  const sanitizeFileName = (value) => {
    const safe = String(value || 'account').trim().replace(/[\\/:*?"<>|]+/g, '_');
    return safe || 'account';
  };

  const buildImportRecord = ({ email, csesidx, configId, secureCSes, hostCOses, expiresAt }) => ({
    id: email,
    secure_c_ses: secureCSes,
    csesidx,
    config_id: configId,
    host_c_oses: hostCOses || '',
    expires_at: expiresAt || '',
  });

  const buildImportJson = (record) => JSON.stringify([record], null, 2);

  const download = (content, filename) => {
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async (text) => {
    if (typeof GM_setClipboard === 'function') {
      GM_setClipboard(text, 'text');
      return;
    }

    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', 'true');
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  };

  const showSetupGuide = (reason = '') => {
    const lines = reason ? [`原因：${reason}`, ...SETUP_GUIDE] : SETUP_GUIDE;
    flashButtonState(SETUP_LABEL, '#f59e0b', SETUP_TITLE);
    window.alert(lines.join('\n'));
  };

  const getEmail = () => {
    let email = localStorage.getItem('gemini_user_email');
    if (!email) {
      email = window.prompt('请输入要导入的账号邮箱：', '') || '';
      email = email.trim();
      if (email) {
        localStorage.setItem('gemini_user_email', email);
      }
    }
    return email?.trim() || '';
  };

  const hasCookieApi = typeof GM_cookie === 'function';
  if (!hasCookieApi) {
    setButtonState(SETUP_LABEL, '#f59e0b', SETUP_TITLE);
  }

  button.addEventListener('click', (event) => {
    if (!hasCookieApi) {
      showSetupGuide('当前脚本无法访问 GM_cookie。');
      return;
    }

    const pathParts = window.location.pathname.split('/');
    const cidIndex = pathParts.indexOf('cid');
    const configId = (cidIndex !== -1 && pathParts[cidIndex + 1]) || '';
    const csesidx = new URLSearchParams(window.location.search).get('csesidx') || '';
    const email = getEmail();
    const shouldDownload = event.shiftKey === true;

    if (!email) {
      flashButtonState(ERROR_LABEL, '#d93025', '请输入邮箱后重试');
      window.alert('请输入账号邮箱后再试。');
      return;
    }

    if (!configId || !csesidx) {
      flashButtonState(ERROR_LABEL, '#d93025', '当前页面缺少导入参数');
      window.alert('未读取到 config_id 或 csesidx，请在 Gemini Business 的有效业务页面使用此脚本。');
      return;
    }

    GM_cookie('list', {}, async (cookies, error) => {
      try {
        if (error) {
          showSetupGuide('读取 Cookie 失败。');
          return;
        }

        const hostCOses = (cookies.find((cookie) => cookie.name === '__Host-C_OSES') || {}).value || '';
        const sesCookie = cookies.find((cookie) => cookie.name === '__Secure-C_SES') || {};
        const secureCSes = sesCookie.value || '';

        if (!secureCSes) {
          showSetupGuide('未读取到 __Secure-C_SES。若已登录，请优先检查 Cookie 权限设置。');
          return;
        }

        const payload = buildImportJson(
          buildImportRecord({
            email,
            csesidx,
            configId,
            secureCSes,
            hostCOses,
            expiresAt: buildExpireAt(),
          }),
        );

        if (shouldDownload) {
          download(payload, `${sanitizeFileName(email)}.json`);
          flashButtonState(DOWNLOAD_LABEL, '#1e8e3e', 'Import JSON downloaded');
          return;
        }

        await copyToClipboard(payload);
        flashButtonState(COPY_LABEL, '#1e8e3e', 'Import JSON copied');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Build failed.';
        flashButtonState(ERROR_LABEL, '#d93025', message);
        window.alert(`Error: ${message}`);
      }
    });
  });
})();
