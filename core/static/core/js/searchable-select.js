(function () {
  'use strict';

  const MAX_VISIBLE_OPTIONS = 100;
  const SEARCHABLE_NAMES = new Set([
    'carrera', 'id_carrera',
    'asignatura', 'id_asignatura',
    'docente', 'id_docente',
    'campo', 'id_campo',
  ]);

  function normalize(value) {
    return String(value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLocaleLowerCase('es')
      .trim();
  }

  function shouldEnhance(select) {
    if (
      select.dataset.searchableReady === 'true'
      || select.dataset.noSearch === 'true'
      || select.multiple
      || select.size > 1
      || select.closest('.searchable-select')
    ) return false;
    return (
      select.dataset.searchableSelect === 'true'
      || SEARCHABLE_NAMES.has(select.name)
      || select.options.length >= 12
    );
  }

  function enhance(select) {
    if (!shouldEnhance(select)) return;
    select.dataset.searchableReady = 'true';
    select.classList.add('searchable-select-native');

    const wrapper = document.createElement('div');
    wrapper.className = 'searchable-select';
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);

    const control = document.createElement('div');
    control.className = 'searchable-select-control';
    wrapper.appendChild(control);

    const input = document.createElement('input');
    input.type = 'search';
    input.className = `form-control searchable-select-input${select.classList.contains('form-select-sm') ? ' form-control-sm' : ''}`;
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.placeholder = select.dataset.searchPlaceholder || 'Escriba para buscar...';
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-haspopup', 'listbox');
    control.appendChild(input);

    const actions = document.createElement('div');
    actions.className = 'searchable-select-actions';
    control.appendChild(actions);

    const clear = document.createElement('button');
    clear.type = 'button';
    clear.className = 'searchable-select-action searchable-select-clear';
    clear.title = 'Limpiar selección';
    clear.setAttribute('aria-label', 'Limpiar selección');
    clear.innerHTML = '<i class="fas fa-xmark" aria-hidden="true"></i>';
    actions.appendChild(clear);

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'searchable-select-action searchable-select-toggle';
    toggle.title = 'Mostrar opciones';
    toggle.setAttribute('aria-label', 'Mostrar opciones');
    toggle.innerHTML = '<i class="fas fa-chevron-down" aria-hidden="true"></i>';
    actions.appendChild(toggle);

    const menu = document.createElement('div');
    menu.className = 'searchable-select-menu';
    menu.hidden = true;
    menu.id = `searchable-${select.id || Math.random().toString(36).slice(2)}`;
    menu.setAttribute('role', 'listbox');
    input.setAttribute('aria-controls', menu.id);
    wrapper.appendChild(menu);

    let activeIndex = -1;
    let renderedOptions = [];
    let internalChange = false;

    function options() {
      return Array.from(select.options).map((option, index) => ({
        option,
        index,
        value: option.value,
        label: option.textContent.trim(),
        search: normalize(`${option.textContent} ${option.value}`),
        disabled: option.disabled,
      }));
    }

    function selectedLabel() {
      const option = select.selectedOptions[0];
      return option && option.value ? option.textContent.trim() : '';
    }

    function syncFromSelect() {
      if (document.activeElement !== input || !wrapper.classList.contains('is-open')) {
        input.value = selectedLabel();
      }
      input.readOnly = select.disabled;
      toggle.disabled = select.disabled;
      clear.disabled = select.disabled;
      clear.hidden = !select.value || select.disabled;
      wrapper.classList.toggle('is-disabled', select.disabled);
    }

    function closeMenu(restoreLabel = true) {
      menu.hidden = true;
      wrapper.classList.remove('is-open');
      input.setAttribute('aria-expanded', 'false');
      activeIndex = -1;
      if (restoreLabel) input.value = selectedLabel();
    }

    function setActive(index) {
      activeIndex = Math.max(0, Math.min(index, renderedOptions.length - 1));
      renderedOptions.forEach((item, itemIndex) => {
        item.button.classList.toggle('is-active', itemIndex === activeIndex);
      });
      const active = renderedOptions[activeIndex];
      if (active) {
        input.setAttribute('aria-activedescendant', active.button.id);
        active.button.scrollIntoView({ block: 'nearest' });
      } else {
        input.removeAttribute('aria-activedescendant');
      }
    }

    function choose(item) {
      if (!item || item.disabled) return;
      internalChange = true;
      select.value = item.value;
      internalChange = false;
      select.dispatchEvent(new Event('change', { bubbles: true }));
      select.dispatchEvent(new Event('input', { bubbles: true }));
      syncFromSelect();
      closeMenu();
      input.focus();
    }

    function render(query = '') {
      const normalizedQuery = normalize(query);
      const allOptions = options();
      const matches = allOptions.filter(item => (
        !normalizedQuery || item.search.includes(normalizedQuery)
      ));
      const visible = matches.slice(0, MAX_VISIBLE_OPTIONS);
      menu.innerHTML = '';
      renderedOptions = [];

      visible.forEach((item, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.id = `${menu.id}-option-${item.index}`;
        button.className = 'searchable-select-option';
        button.textContent = item.label || 'Sin selección';
        button.setAttribute('role', 'option');
        button.setAttribute('aria-selected', String(item.value === select.value));
        button.classList.toggle('is-selected', item.value === select.value);
        button.disabled = item.disabled;
        button.addEventListener('mousedown', event => event.preventDefault());
        button.addEventListener('click', () => choose(item));
        menu.appendChild(button);
        renderedOptions.push({ item, button });
        if (item.value === select.value) activeIndex = index;
      });

      if (!visible.length) {
        const empty = document.createElement('div');
        empty.className = 'searchable-select-empty';
        empty.textContent = 'No se encontraron coincidencias.';
        menu.appendChild(empty);
        activeIndex = -1;
      } else if (matches.length > MAX_VISIBLE_OPTIONS) {
        const hint = document.createElement('div');
        hint.className = 'searchable-select-hint';
        hint.textContent = `Hay ${matches.length} resultados. Escriba más para precisar la búsqueda.`;
        menu.appendChild(hint);
      }
      setActive(activeIndex >= 0 ? activeIndex : 0);
    }

    function openMenu(selectText = false) {
      if (select.disabled) return;
      menu.hidden = false;
      wrapper.classList.add('is-open');
      input.setAttribute('aria-expanded', 'true');
      if (selectText) input.select();
      render(selectText ? '' : input.value);
    }

    input.addEventListener('focus', () => openMenu(true));
    input.addEventListener('click', () => openMenu(false));
    input.addEventListener('input', () => {
      if (menu.hidden) openMenu(false);
      render(input.value);
    });
    input.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (menu.hidden) openMenu(false);
        else setActive(activeIndex + 1);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        if (menu.hidden) openMenu(false);
        else setActive(activeIndex - 1);
      } else if (event.key === 'Enter' && !menu.hidden) {
        event.preventDefault();
        choose(renderedOptions[activeIndex]?.item);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        closeMenu();
      } else if (event.key === 'Tab') {
        closeMenu();
      }
    });

    toggle.addEventListener('click', () => {
      if (menu.hidden) {
        input.focus();
        openMenu(true);
      } else {
        closeMenu();
      }
    });
    clear.addEventListener('click', () => {
      const emptyOption = options().find(item => item.value === '');
      if (emptyOption) choose(emptyOption);
      else {
        select.selectedIndex = -1;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        syncFromSelect();
      }
    });
    select.addEventListener('change', syncFromSelect);
    select.addEventListener('input', syncFromSelect);
    select.addEventListener('invalid', event => {
      event.preventDefault();
      input.focus();
      openMenu(true);
    });

    const label = select.id
      ? document.querySelector(`label[for="${CSS.escape(select.id)}"]`)
      : null;
    label?.addEventListener('click', event => {
      event.preventDefault();
      input.focus();
    });

    const observer = new MutationObserver(() => {
      if (internalChange) return;
      syncFromSelect();
      if (!menu.hidden) render(input.value);
    });
    observer.observe(select, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['disabled', 'selected', 'label'],
    });

    document.addEventListener('mousedown', event => {
      if (!wrapper.contains(event.target)) closeMenu();
    });
    syncFromSelect();
  }

  function initialize(root = document) {
    root.querySelectorAll('select.form-select').forEach(enhance);
  }

  document.addEventListener('DOMContentLoaded', () => initialize());
  window.SearchableSelect = { initialize };
})();
