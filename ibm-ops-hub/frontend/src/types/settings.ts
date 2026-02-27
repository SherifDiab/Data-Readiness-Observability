export type SettingFieldType = 'url' | 'text' | 'password' | 'boolean' | 'number' | 'tags';

export interface SettingFieldDef {
  key: string;
  label: string;
  type: SettingFieldType;
  required?: boolean;
  sensitive?: boolean;
  hint?: string;
  min?: number;
  max?: number;
}

export interface SettingsSchema {
  [category: string]: SettingFieldDef[];
}

export interface SettingsResponse {
  schema: SettingsSchema;
  values: Record<string, unknown>;
  overrides: string[];
}

export interface SettingsUpdateResult {
  status: string;
  applied: string[];
  skipped: string[];
}
