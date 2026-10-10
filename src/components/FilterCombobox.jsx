import { useId, useMemo, useRef, useState } from 'react';

const MAX_OPTIONS = 50;

// A type-to-filter multi-select. `options` are { value, label, hint?, count? };
// the chosen values show as removable chips inside the field.
export default function FilterCombobox({ label, placeholder, options, selected, onChange }) {
  const [text, setText] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const inputRef = useRef(null);
  const listId = useId();

  const matches = useMemo(() => {
    const chosen = new Set(selected);
    const q = text.trim().toLowerCase();
    const out = [];
    for (const o of options) {
      if (chosen.has(o.value)) continue;
      if (
        q &&
        !o.label.toLowerCase().includes(q) &&
        !(o.hint || '').toLowerCase().includes(q)
      ) {
        continue;
      }
      out.push(o);
      if (out.length === MAX_OPTIONS) break;
    }
    return out;
  }, [options, selected, text]);

  function add(value) {
    onChange([...selected, value]);
    setText('');
    setActive(0);
    inputRef.current?.focus();
  }

  function remove(value) {
    onChange(selected.filter((v) => v !== value));
  }

  function onKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, matches.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      if (open && matches[active]) {
        e.preventDefault();
        add(matches[active].value);
      }
    } else if (e.key === 'Escape') {
      setOpen(false);
    } else if (e.key === 'Backspace' && !text && selected.length) {
      remove(selected[selected.length - 1]);
    }
  }

  const showList = open && matches.length > 0;

  return (
    <div className="relative min-w-0">
      <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-muted-2">{label}</div>
      <div
        className="flex min-h-[46px] flex-wrap items-center gap-1.5 rounded-[10px] border border-border-input bg-white px-2.5 py-1.5 focus-within:border-accent"
        onClick={() => inputRef.current?.focus()}
      >
        {selected.map((v) => (
          <span
            key={v}
            className="flex max-w-full items-center gap-1 rounded-full border border-accent-border bg-accent-bg px-2.5 py-1 text-[12px] font-semibold text-accent-hover"
          >
            <span className="truncate">{v}</span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                remove(v);
              }}
              aria-label={`Remove ${v}`}
              className="text-sm font-extrabold leading-none"
            >
              ×
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          type="text"
          role="combobox"
          aria-label={label}
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={showList ? `${listId}-${active}` : undefined}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setActive(0);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
          placeholder={selected.length ? 'Add another…' : placeholder}
          className="min-w-[90px] flex-1 bg-transparent px-1 py-1.5 text-sm text-ink outline-none"
        />
      </div>

      {showList && (
        <ul
          id={listId}
          role="listbox"
          aria-multiselectable="true"
          className="absolute left-0 right-0 top-full z-30 mt-1 max-h-72 overflow-auto rounded-[10px] border border-border-input bg-white py-1 shadow-lg"
        >
          {matches.map((o, i) => (
            <li
              key={o.value}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === active}
              // mousedown, not click: the input's blur would close the list first
              onMouseDown={(e) => {
                e.preventDefault();
                add(o.value);
              }}
              onMouseEnter={() => setActive(i)}
              className={`flex cursor-pointer items-baseline justify-between gap-3 px-3 py-2 text-[13px] ${
                i === active ? 'bg-accent-bg' : ''
              }`}
            >
              <span className="min-w-0">
                <span className="font-semibold text-ink">{o.label}</span>
                {o.hint && <span className="ml-2 text-muted-2">{o.hint}</span>}
              </span>
              {o.count != null && <span className="flex-none text-[11.5px] text-muted-3">{o.count}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
