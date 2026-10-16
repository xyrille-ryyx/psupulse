/* PSU Pulse — small UI behaviours shared by every page. */
(function () {
  const EYE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>';
  const EYE_OFF = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9.9 4.2A10.8 10.8 0 0 1 12 4c6.5 0 10 8 10 8a17.6 17.6 0 0 1-2.2 3.2M6.6 6.6C3.9 8.4 2 12 2 12s3.5 8 10 8a9.7 9.7 0 0 0 5.4-1.6"/><path d="M14.1 14.1a3 3 0 0 1-4.2-4.2"/><path d="m2 2 20 20"/></svg>';

  // 1. Show / hide password: every password field gets an eye button.
  function addPasswordToggles() {
    document.querySelectorAll('input[type="password"]').forEach((input) => {
      if (input.dataset.toggle === 'done') return;
      input.dataset.toggle = 'done';
      const wrap = document.createElement('div');
      wrap.className = 'pw-field';
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pw-toggle';
      btn.setAttribute('aria-label', 'Show password');
      btn.innerHTML = EYE;
      btn.addEventListener('click', () => {
        const show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        btn.innerHTML = show ? EYE_OFF : EYE;
        btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
        input.focus({ preventScroll: true });
      });
      wrap.appendChild(btn);
    });
  }

  // 2. Notifications fade out after 3 seconds (and can be closed sooner).
  function autoDismissFlashes() {
    document.querySelectorAll('.flash').forEach((flash) => {
      const close = document.createElement('button');
      close.type = 'button';
      close.className = 'flash-close';
      close.setAttribute('aria-label', 'Dismiss notification');
      close.innerHTML = '&times;';
      flash.appendChild(close);
      const hide = () => {
        flash.classList.add('flash-hide');
        setTimeout(() => {
          const box = flash.parentElement;
          flash.remove();
          if (box && !box.children.length) box.remove();
        }, 350);
      };
      close.addEventListener('click', hide);
      setTimeout(hide, 3000);
    });
  }

  // 3. "Remember me": keep the username on this device (never the password).
  function rememberUsername() {
    const form = document.querySelector('form[data-remember]');
    if (!form) return;
    const user = form.querySelector('input[name="username"]');
    const box = form.querySelector('input[name="remember"]');
    const KEY = 'psupulse.username';
    try {
      const saved = localStorage.getItem(KEY);
      if (saved && !user.value) {
        user.value = saved;
        box.checked = true;
        const pw = form.querySelector('input[name="password"]');
        if (pw) pw.focus();
      }
    } catch (e) { /* storage blocked: nothing to restore */ }
    form.addEventListener('submit', () => {
      try {
        if (box.checked) localStorage.setItem(KEY, user.value.trim());
        else localStorage.removeItem(KEY);
      } catch (e) { /* storage blocked: sign-in still works */ }
    });
  }

  // 4. Expand / collapse the navigation rail; the choice is remembered on this device.
  function railToggle() {
    const btn = document.getElementById('rail-toggle');
    if (!btn) return;
    const root = document.documentElement;
    const sync = () => {
      const open = root.classList.contains('rail-open');
      btn.setAttribute('aria-expanded', String(open));
      btn.setAttribute('aria-label', open ? 'Collapse menu' : 'Expand menu');
      btn.dataset.tip = open ? 'Collapse menu' : 'Expand menu';
    };
    sync();
    btn.addEventListener('click', () => {
      root.classList.toggle('rail-open');
      try { localStorage.setItem('psupulse.rail', root.classList.contains('rail-open') ? 'open' : 'closed'); } catch (e) { /* not saved */ }
      sync();
    });
    // Let charts re-fit once the width animation has finished.
    const rail = document.getElementById('rail');
    if (rail) rail.addEventListener('transitionend', (e) => {
      if (e.target === rail && e.propertyName === 'width') window.dispatchEvent(new Event('resize'));
    });
  }

  // Tooltips for the collapsed rail. One fixed element, so the scrolling link list can't clip it.
  function railTooltips() {
    const links = document.querySelectorAll('.rail a[data-tip]');
    if (!links.length) return;
    const tip = document.createElement('div');
    tip.className = 'rail-tip';
    tip.setAttribute('role', 'tooltip');
    tip.hidden = true;
    document.body.appendChild(tip);
    const hide = () => { tip.hidden = true; };
    const show = (e) => {
      if (document.documentElement.classList.contains('rail-open')) return;
      const box = e.currentTarget.getBoundingClientRect();
      tip.textContent = e.currentTarget.dataset.tip;
      tip.style.left = `${box.right + 12}px`;
      tip.style.top = `${box.top + box.height / 2}px`;
      tip.hidden = false;
    };
    links.forEach((a) => {
      a.addEventListener('mouseenter', show);
      a.addEventListener('focus', show);
      a.addEventListener('mouseleave', hide);
      a.addEventListener('blur', hide);
    });
    const nav = document.querySelector('.rail-nav');
    if (nav) nav.addEventListener('scroll', hide);
  }

  // Unit picker: live "N selected" count and a search that keeps matches' parent units visible.
  function unitPickers() {
    document.querySelectorAll('[data-unit-picker]').forEach((picker) => {
      const boxes = picker.querySelectorAll('input[type=checkbox]');
      const count = picker.querySelector('[data-unit-count]');
      const search = picker.querySelector('[data-unit-search]');
      const empty = picker.querySelector('.unit-empty');
      const groups = picker.querySelectorAll('.unit-group');
      const updateCount = () => {
        const n = [...boxes].filter((b) => b.checked).length;
        count.textContent = n ? `${n} selected` : 'None selected';
      };
      const filter = () => {
        const q = search.value.trim().toLowerCase();
        // A node shows when it, a parent, or a child matches.
        const matches = (node) => node.querySelector(':scope > .unit-row').textContent.toLowerCase().includes(q);
        let any = false;
        picker.querySelectorAll('.unit-node').forEach((node) => {
          let show = !q || matches(node);
          for (let up = node.parentElement.closest('.unit-node'); !show && up; up = up.parentElement.closest('.unit-node')) {
            show = matches(up);
          }
          if (!show) show = [...node.querySelectorAll('.unit-node')].some(matches);
          node.hidden = !show;
          any = any || show;
        });
        groups.forEach((g) => { g.hidden = ![...g.nextElementSibling.children].some((n) => !n.hidden); });
        empty.hidden = any;
      };
      // Ticking a college or department ticks everything under it; unticking one unit unticks
      // its parents. A parent with only some units ticked shows the "partly selected" dash.
      const boxOf = (node) => node.querySelector(':scope > .unit-row input');
      const markPartial = () => {
        picker.querySelectorAll('.unit-node').forEach((node) => {
          const box = boxOf(node);
          box.indeterminate = !box.checked && !!node.querySelector('.unit-node input:checked');
        });
      };
      boxes.forEach((b) => b.addEventListener('change', () => {
        const node = b.closest('.unit-node');
        node.querySelectorAll('.unit-node input').forEach((child) => { child.checked = b.checked; });
        if (!b.checked) {
          for (let up = node.parentElement.closest('.unit-node'); up; up = up.parentElement.closest('.unit-node')) {
            boxOf(up).checked = false;
          }
        }
        markPartial();
        updateCount();
      }));
      markPartial();
      search.addEventListener('input', filter);
      // Enter in the search box shouldn't submit the user form.
      search.addEventListener('keydown', (e) => { if (e.key === 'Enter') e.preventDefault(); });
      updateCount();
    });
  }

  // 5. Custom dropdowns: a styled, searchable list on top of each native <select>.
  //    The native select stays in the form (hidden) and still submits / fires "change".
  const CHEVRON = '<svg class="cs-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  const CHECK = '<svg class="cs-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  const SEARCH = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>';
  let openDropdown = null;
  let dropdownCount = 0;

  function enhanceSelect(select) {
    if (select.dataset.enhanced) return;
    select.dataset.enhanced = '1';
    const id = 'cs-' + (++dropdownCount);
    const label = select.id ? document.querySelector(`label[for="${select.id}"]`) : null;

    // Leading em-spaces in an option mark its depth (college > department > course).
    const options = [...select.options].map((o, index) => {
      const raw = o.textContent.replace(/^[ \t\r\n]+/, '');
      const level = (raw.match(/^ */) || [''])[0].length;
      return { index, value: o.value, text: raw.replace(/^[ \s]+/, '').trim(), level, disabled: o.disabled };
    });

    const wrap = document.createElement('div');
    wrap.className = 'cs' + (select.closest('.filters') ? ' cs-pill' : '');
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);
    select.tabIndex = -1;
    select.setAttribute('aria-hidden', 'true');

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'cs-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', id);
    if (label) { label.id = label.id || id + '-label'; trigger.setAttribute('aria-labelledby', label.id + ' ' + id + '-value'); }
    trigger.innerHTML = `<span class="cs-value" id="${id}-value"></span>${CHEVRON}`;
    if (label) label.addEventListener('click', (e) => { e.preventDefault(); trigger.focus(); });

    const panel = document.createElement('div');
    panel.className = 'cs-panel';
    panel.hidden = true;
    const searchable = options.length > 8;
    panel.innerHTML = (searchable
      ? `<div class="cs-search">${SEARCH}<input type="text" placeholder="Search…" aria-label="Search options" autocomplete="off"></div>`
      : '') + `<ul class="cs-list" role="listbox" id="${id}" tabindex="-1"></ul><p class="cs-empty" hidden>No matches</p>`;
    wrap.appendChild(trigger);
    wrap.appendChild(panel);

    const list = panel.querySelector('.cs-list');
    const search = panel.querySelector('.cs-search input');
    const empty = panel.querySelector('.cs-empty');
    options.forEach((o) => {
      const li = document.createElement('li');
      li.className = 'cs-option' + (o.level ? ` cs-level-${Math.min(o.level, 3)}` : '') + (o.level === 0 && options.some((x) => x.level > 0) && o.value !== 'all' ? ' cs-group' : '');
      li.id = `${id}-opt-${o.index}`;
      li.setAttribute('role', 'option');
      li.dataset.index = o.index;
      if (o.disabled) li.setAttribute('aria-disabled', 'true');
      li.innerHTML = `<span class="cs-text"></span>${CHECK}`;
      li.querySelector('.cs-text').textContent = o.text;
      list.appendChild(li);
    });
    const items = [...list.children];
    let active = -1;

    const render = () => {
      const current = options[select.selectedIndex];
      trigger.querySelector('.cs-value').textContent = current ? current.text : '';
      items.forEach((li) => li.setAttribute('aria-selected', String(Number(li.dataset.index) === select.selectedIndex)));
    };
    const visible = () => items.filter((li) => !li.hidden && li.getAttribute('aria-disabled') !== 'true');
    const setActive = (li) => {
      items.forEach((x) => x.classList.remove('is-active'));
      active = li ? items.indexOf(li) : -1;
      if (li) { li.classList.add('is-active'); li.scrollIntoView({ block: 'nearest' }); list.setAttribute('aria-activedescendant', li.id); }
    };
    const open = () => {
      if (openDropdown && openDropdown !== close) openDropdown();
      panel.hidden = false;
      wrap.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
      openDropdown = close;
      setActive(items[select.selectedIndex]);
      (search || list).focus({ preventScroll: true });
    };
    function close(focusTrigger) {
      panel.hidden = true;
      wrap.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
      if (search) { search.value = ''; filter(''); }
      if (openDropdown === close) openDropdown = null;
      if (focusTrigger) trigger.focus({ preventScroll: true });
    }
    const choose = (li) => {
      if (!li || li.getAttribute('aria-disabled') === 'true') return;
      const index = Number(li.dataset.index);
      const changed = index !== select.selectedIndex;
      select.selectedIndex = index;
      render();
      close(true);
      if (changed) select.dispatchEvent(new Event('change', { bubbles: true }));
    };
    function filter(q) {
      const term = q.trim().toLowerCase();
      items.forEach((li, i) => { li.hidden = term && !options[i].text.toLowerCase().includes(term); });
      empty.hidden = visible().length > 0;
      setActive(visible()[0] || null);
    }
    const onKey = (e) => {
      const vis = visible();
      const pos = vis.indexOf(items[active]);
      if (e.key === 'ArrowDown') { e.preventDefault(); setActive(vis[Math.min(pos + 1, vis.length - 1)] || vis[0]); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(vis[Math.max(pos - 1, 0)] || vis[0]); }
      else if (e.key === 'Home') { e.preventDefault(); setActive(vis[0]); }
      else if (e.key === 'End') { e.preventDefault(); setActive(vis[vis.length - 1]); }
      else if (e.key === 'Enter') { e.preventDefault(); choose(items[active]); }
      else if (e.key === 'Escape') { e.preventDefault(); close(true); }
      else if (e.key === 'Tab') { close(false); }
    };

    trigger.addEventListener('click', () => (panel.hidden ? open() : close(true)));
    trigger.addEventListener('keydown', (e) => {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); open(); }
    });
    list.addEventListener('keydown', onKey);
    if (search) { search.addEventListener('keydown', onKey); search.addEventListener('input', () => filter(search.value)); }
    list.addEventListener('mousemove', (e) => { const li = e.target.closest('.cs-option'); if (li && !li.classList.contains('is-active')) setActive(li); });
    list.addEventListener('click', (e) => choose(e.target.closest('.cs-option')));
    document.addEventListener('mousedown', (e) => { if (!panel.hidden && !wrap.contains(e.target)) close(false); });
    select.addEventListener('change', render);
    render();
  }

  function enhanceSelects() {
    document.querySelectorAll('select:not([multiple]):not([data-native])').forEach(enhanceSelect);
  }

  document.addEventListener('DOMContentLoaded', () => {
    enhanceSelects();
    railToggle();
    railTooltips();
    unitPickers();
    addPasswordToggles();
    autoDismissFlashes();
    rememberUsername();
  });
})();
