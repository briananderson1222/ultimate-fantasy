"use client";

import React from "react";
import { Card } from "../primitives/Card";
import { Button } from "../primitives/Button";
import { cn } from "../../../lib/utils";

export interface SettingItem {
  id: string;
  title: string;
  description: string;
  value: string | number | boolean | Date;
  type: "text" | "number" | "boolean" | "select" | "date" | "datetime";
  options?: string[];
  min?: number;
  max?: number;
  error?: string;
  category?: string;
}

export interface SettingAction {
  label: string;
  action: () => void;
}

export interface SettingsWithCategory {
  category: string;
  items: SettingItem[];
}

export interface SettingsGridProps {
  settings: SettingItem[] | SettingsWithCategory[];
  variant?: "default" | "compact";
  readOnly?: boolean;
  actions?: SettingAction[];
  onChange?: (settingId: string, value: any) => void;
  className?: string;
}

const SettingControl: React.FC<{
  setting: SettingItem;
  readOnly?: boolean;
  onChange?: (value: any) => void;
}> = ({ setting, readOnly = false, onChange }) => {
  const { id, type, value, options, min, max, error } = setting;

  const handleChange = (newValue: any) => {
    if (!readOnly && onChange) {
      onChange(newValue);
    }
  };

  const baseInputClasses = cn(
    "w-full px-3 py-2 border rounded-lg text-sm",
    "focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
    error && "border-red-500",
    readOnly && "bg-gray-50 cursor-not-allowed",
  );

  switch (type) {
    case "boolean":
      return (
        <div className="flex items-center">
          <input
            type="checkbox"
            id={id}
            checked={Boolean(value)}
            disabled={readOnly}
            onChange={(e) => handleChange(e.target.checked)}
            className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <label htmlFor={id} className="sr-only">
            {setting.title}
          </label>
        </div>
      );

    case "select":
      return (
        <select
          value={String(value)}
          disabled={readOnly}
          onChange={(e) => handleChange(e.target.value)}
          className={baseInputClasses}
        >
          {options?.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );

    case "number":
      return (
        <input
          type="number"
          value={String(value)}
          min={min}
          max={max}
          disabled={readOnly}
          onChange={(e) => handleChange(Number(e.target.value))}
          className={baseInputClasses}
        />
      );

    case "date":
      const dateValue = value instanceof Date ? value.toISOString().split("T")[0] : String(value);
      return (
        <input
          type="date"
          value={dateValue}
          disabled={readOnly}
          onChange={(e) => handleChange(e.target.value)}
          className={baseInputClasses}
        />
      );

    case "datetime":
      const datetimeValue =
        value instanceof Date ? value.toISOString().slice(0, 16) : String(value).slice(0, 16);
      return (
        <input
          type="datetime-local"
          value={datetimeValue}
          disabled={readOnly}
          onChange={(e) => handleChange(e.target.value)}
          className={baseInputClasses}
        />
      );

    case "text":
    default:
      return (
        <input
          type="text"
          value={String(value)}
          disabled={readOnly}
          onChange={(e) => handleChange(e.target.value)}
          className={baseInputClasses}
        />
      );
  }
};

const SettingRow: React.FC<{
  setting: SettingItem;
  variant?: "default" | "compact";
  readOnly?: boolean;
  onChange?: (value: any) => void;
}> = ({ setting, variant = "default", readOnly = false, onChange }) => {
  const { title, description, error } = setting;

  if (variant === "compact") {
    return (
      <div className="flex items-center justify-between py-2">
        <div className="flex-1 min-w-0 mr-4">
          <div className="font-medium text-sm">{title}</div>
          <div className="text-xs text-muted-foreground truncate">{description}</div>
        </div>
        <div className="flex-shrink-0 w-32">
          <SettingControl setting={setting} readOnly={readOnly} onChange={onChange} />
          {error && <div className="text-xs text-red-600 mt-1">{error}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div>
        <div className="font-medium">{title}</div>
        <div className="text-sm text-muted-foreground">{description}</div>
      </div>
      <SettingControl setting={setting} readOnly={readOnly} onChange={onChange} />
      {error && <div className="text-sm text-red-600">{error}</div>}
    </div>
  );
};

export const SettingsGrid: React.FC<SettingsGridProps> = ({
  settings,
  variant = "default",
  readOnly = false,
  actions,
  onChange,
  className,
}) => {
  const handleSettingChange = (settingId: string, value: any) => {
    if (onChange) {
      onChange(settingId, value);
    }
  };

  // Check if settings have categories
  const hasCategories = settings.length > 0 && "category" in settings[0];

  return (
    <Card className={className}>
      <Card.Header>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Settings</h3>
          {actions && actions.length > 0 && (
            <div className="flex gap-2">
              {actions.map((action, index) => (
                <Button key={index} variant="outline" size="sm" onClick={action.action}>
                  {action.label}
                </Button>
              ))}
            </div>
          )}
        </div>
      </Card.Header>

      <Card.Content>
        {hasCategories ? (
          // Render categorized settings
          <div className="space-y-6">
            {(settings as SettingsWithCategory[]).map((categoryGroup) => (
              <div key={categoryGroup.category} className="space-y-4">
                <h4 className="text-lg font-semibold border-b pb-2">{categoryGroup.category}</h4>
                <div className={cn(variant === "compact" ? "space-y-1" : "space-y-4")}>
                  {categoryGroup.items.map((setting) => (
                    <SettingRow
                      key={setting.id}
                      setting={setting}
                      variant={variant}
                      readOnly={readOnly}
                      onChange={(value) => handleSettingChange(setting.id, value)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Render flat settings
          <div className={cn(variant === "compact" ? "space-y-1" : "space-y-4")}>
            {(settings as SettingItem[]).map((setting) => (
              <SettingRow
                key={setting.id}
                setting={setting}
                variant={variant}
                readOnly={readOnly}
                onChange={(value) => handleSettingChange(setting.id, value)}
              />
            ))}
          </div>
        )}
      </Card.Content>
    </Card>
  );
};
