import { useState, useEffect, useCallback } from 'react';
import { Save, RefreshCw, CheckCircle, AlertCircle, X, RotateCcw } from 'lucide-react';
import { fetchSettings, updateSettings, refreshComponent } from '../../services/api';
import type { SettingsResponse, SettingFieldDef } from '../../types/settings';

const CATEGORY_LABELS: Record<string, string> = {
  cpd: 'CPD Connection',
  datastage: 'DataStage',
  flink: 'Flink',
  event_processing: 'Event Processing',
  apic: 'API Connect',
  polling: 'Polling Intervals',
  general: 'General',
};

// Fields whose placeholder dots mean "value set, not changed"
const PLACEHOLDER = '••••••••';

export default function SettingsPage() {
  const [serverData, setServerData] = useState<SettingsResponse | null>(null);
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [activeTab, setActiveTab] = useState<string>('cpd');
  const [isSaving, setSaving] = useState(false);
  const [isLoading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const loadSettings = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchSettings();
      setServerData(data);
      setFormValues(data.values as Record<string, unknown>);
      const cats = Object.keys(data.schema);
      if (cats.length > 0) setActiveTab(prev => (cats.includes(prev) ? prev : cats[0]));
    } catch {
      setFeedback({ type: 'error', message: 'Failed to load settings from server.' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  function handleChange(key: string, value: unknown) {
    setFormValues(prev => ({ ...prev, [key]: value }));
  }

  async function handleSave() {
    if (!serverData) return;
    try {
      setSaving(true);
      const changes: Record<string, unknown> = {};
      for (const [key, val] of Object.entries(formValues)) {
        // Skip unchanged sensitive placeholders
        if (val === PLACEHOLDER) continue;
        changes[key] = val;
      }
      const result = await updateSettings(changes as Record<string, string | number | boolean | null>);
      const msg =
        result.applied.length > 0
          ? `Saved ${result.applied.length} setting(s): ${result.applied.join(', ')}`
          : 'No changes were applied.';
      setFeedback({ type: 'success', message: msg });
      await loadSettings();
    } catch {
      setFeedback({ type: 'error', message: 'Failed to save settings. Please try again.' });
    } finally {
      setSaving(false);
    }
  }

  async function handleRefreshComponent(component: string) {
    try {
      setRefreshing(component);
      await refreshComponent(component);
      setFeedback({ type: 'success', message: `Triggered re-poll for ${component}.` });
    } catch {
      setFeedback({ type: 'error', message: `Failed to trigger refresh for ${component}.` });
    } finally {
      setRefreshing(null);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-text-secondary">
        <RefreshCw size={20} className="animate-spin mr-2" />
        Loading settings…
      </div>
    );
  }

  if (!serverData) {
    return (
      <div className="p-8 text-status-failed flex items-center gap-2">
        <AlertCircle size={18} />
        Could not load settings.
      </div>
    );
  }

  const categories = Object.entries(serverData.schema);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
          <p className="text-sm text-text-secondary mt-1">
            Configure IBM Ops Hub connections, polling intervals, and feature flags.
            Changes are persisted in Redis and take effect immediately.
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 px-4 py-2 bg-accent text-bg-primary rounded-lg hover:bg-accent/90 disabled:opacity-50 transition-colors font-medium text-sm whitespace-nowrap"
        >
          <Save size={15} />
          {isSaving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>

      {/* Feedback toast */}
      {feedback && (
        <div
          className={`flex items-center gap-3 p-3 rounded-lg mb-5 border ${
            feedback.type === 'success'
              ? 'bg-status-completed/10 border-status-completed/30 text-status-completed'
              : 'bg-status-failed/10 border-status-failed/30 text-status-failed'
          }`}
        >
          {feedback.type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
          <span className="text-sm flex-1">{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="opacity-60 hover:opacity-100">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Category tabs */}
      <div className="flex gap-0 border-b border-border-color mb-6 overflow-x-auto">
        {categories.map(([cat]) => (
          <button
            key={cat}
            onClick={() => setActiveTab(cat)}
            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${
              activeTab === cat
                ? 'border-accent text-accent'
                : 'border-transparent text-text-secondary hover:text-text-primary hover:border-border-color'
            }`}
          >
            {CATEGORY_LABELS[cat] ?? cat}
          </button>
        ))}
      </div>

      {/* Active category fields */}
      {categories.map(([cat, fields]) =>
        cat !== activeTab ? null : (
          <div key={cat} className="space-y-4">
            {/* Quick-refresh button for service categories */}
            {['spark', 'datastage', 'flink', 'event_processing', 'apic'].includes(cat) && (
              <div className="flex justify-end">
                <button
                  onClick={() => handleRefreshComponent(cat)}
                  disabled={refreshing === cat}
                  className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors px-3 py-1.5 border border-border-color rounded-md hover:border-accent/50"
                >
                  <RotateCcw size={12} className={refreshing === cat ? 'animate-spin' : ''} />
                  Force re-poll now
                </button>
              </div>
            )}

            {fields.map(field => (
              <SettingField
                key={field.key}
                field={field}
                value={formValues[field.key]}
                isOverridden={serverData.overrides.includes(field.key)}
                onChange={v => handleChange(field.key, v)}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Field renderer
// ---------------------------------------------------------------------------

function SettingField({
  field,
  value,
  isOverridden,
  onChange,
}: {
  field: SettingFieldDef;
  value: unknown;
  isOverridden: boolean;
  onChange: (v: unknown) => void;
}) {
  const strVal = value !== null && value !== undefined ? String(value) : '';

  return (
    <div className="bg-bg-secondary border border-border-color rounded-lg p-4">
      <div className="flex items-center gap-2 mb-1">
        <label className="text-sm font-medium text-text-primary">
          {field.label}
          {field.required && <span className="text-status-failed ml-1">*</span>}
        </label>
        {isOverridden && (
          <span className="text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded font-mono">
            overridden
          </span>
        )}
        <span className="text-xs text-text-tertiary font-mono ml-auto">{field.key}</span>
      </div>

      {field.hint && <p className="text-xs text-text-tertiary mb-3">{field.hint}</p>}

      {field.type === 'boolean' ? (
        <BooleanToggle value={!!value} onChange={onChange} />
      ) : field.type === 'tags' ? (
        <TagsInput value={strVal} onChange={onChange} />
      ) : field.type === 'number' ? (
        <div className="flex items-center gap-3">
          <input
            type="number"
            value={strVal}
            min={field.min}
            max={field.max}
            onChange={e => onChange(Number(e.target.value))}
            className="w-36 bg-bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent"
          />
          {field.min !== undefined && field.max !== undefined && (
            <span className="text-xs text-text-tertiary">
              {field.min}–{field.max} seconds
            </span>
          )}
        </div>
      ) : (
        <input
          type={field.type === 'password' ? 'password' : field.type === 'url' ? 'url' : 'text'}
          value={strVal}
          placeholder={
            field.type === 'password' && strVal === PLACEHOLDER
              ? 'Enter new value to change'
              : field.type === 'url'
              ? 'https://…'
              : ''
          }
          autoComplete={field.type === 'password' ? 'new-password' : 'off'}
          onChange={e => onChange(e.target.value)}
          className="w-full bg-bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent font-mono"
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Boolean toggle
// ---------------------------------------------------------------------------

function BooleanToggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        role="switch"
        aria-checked={value}
        onClick={() => onChange(!value)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1 focus:ring-offset-bg-secondary ${
          value ? 'bg-accent' : 'bg-bg-hover'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
            value ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
      <span className="text-sm text-text-secondary">{value ? 'Enabled' : 'Disabled'}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tags input (for CPD_PROJECT_IDS)
// ---------------------------------------------------------------------------

function TagsInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [inputVal, setInputVal] = useState('');

  const tags = value ? value.split(',').map(t => t.trim()).filter(Boolean) : [];

  function addTag() {
    const trimmed = inputVal.trim().replace(/,/g, '');
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed].join(','));
    }
    setInputVal('');
  }

  function removeTag(tag: string) {
    onChange(tags.filter(t => t !== tag).join(','));
  }

  return (
    <div className="space-y-2">
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map(tag => (
            <span
              key={tag}
              className="flex items-center gap-1.5 bg-accent/10 text-accent text-xs px-2.5 py-1 rounded-md font-mono"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="hover:text-accent/60 transition-colors"
              >
                <X size={11} />
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <input
          type="text"
          value={inputVal}
          onChange={e => setInputVal(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ',') {
              e.preventDefault();
              addTag();
            }
          }}
          placeholder="Type a project ID and press Enter"
          className="flex-1 bg-bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent font-mono"
        />
        <button
          type="button"
          onClick={addTag}
          className="px-3 py-1.5 bg-accent/10 text-accent rounded-md text-sm hover:bg-accent/20 transition-colors font-medium"
        >
          Add
        </button>
      </div>
      {tags.length === 0 && (
        <p className="text-xs text-text-tertiary">
          No project IDs configured. Add at least one, or set a Single Project ID.
        </p>
      )}
    </div>
  );
}
