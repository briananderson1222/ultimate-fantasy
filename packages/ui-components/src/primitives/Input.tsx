import React from "react";
import { UIComponent, UIComponentProps } from "../models/UIComponent";
import { PlatformAdapter } from "../adapters/platform";

export interface InputProps extends UIComponentProps {
  error?: string;
  label?: string;
  value?: string;
  placeholder?: string;
  onChangeText?: (text: string) => void;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  type?: string;
  name?: string;
  id?: string;
  className?: string;
}

export class Input extends UIComponent<InputProps> {
  getWebStyles() {
    const { error, className } = this.props;

    const baseStyles = "w-full rounded-[var(--radius-md)] border px-[var(--space-3)] py-[var(--space-2)] transition-all duration-[var(--anim-duration-xs)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)] hover:border-[var(--color-muted)]";

    const errorStyles = error
      ? "border-red-500 focus:border-red-500"
      : "border-[var(--border)] focus:border-[var(--ring)]";

    return `${baseStyles} ${errorStyles} ${className || ""}`;
  }

  getNativeStyles() {
    const { error } = this.props;

    return {
      width: "100%",
      borderRadius: 8,
      borderWidth: 1,
      borderColor: error ? "#ef4444" : "#d1d5db",
      paddingHorizontal: 12,
      paddingVertical: 8,
      fontSize: 14,
      backgroundColor: "#ffffff",
      color: "#374151",
    };
  }

  render() {
    const {
      error,
      label,
      value,
      placeholder,
      onChangeText,
      onChange,
      disabled,
      type = "text",
      name,
      id,
      className,
      ...otherProps
    } = this.props;

    if (PlatformAdapter.getCurrentPlatform() === "web") {
      const inputId = id || name || Math.random().toString(36).slice(2);
      const describedById = error ? `${inputId}-error` : undefined;

      const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange?.(e);
        onChangeText?.(e.target.value);
      };

      return (
        <div className="space-y-1">
          {label && (
            <label htmlFor={inputId} className="block text-sm text-[var(--color-muted)]">
              {label}
            </label>
          )}
          <input
            id={inputId}
            name={name}
            type={type}
            value={value}
            placeholder={placeholder}
            onChange={handleChange}
            disabled={disabled}
            className={this.getWebStyles()}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedById}
            {...otherProps}
          />
          {error && (
            <p id={describedById} className="animate-slide-up text-xs text-red-600">
              {error}
            </p>
          )}
        </div>
      );
    }

    // React Native implementation
    const React = require('react');
    const { View, Text, TextInput } = require('react-native');

    const inputId = id || name || Math.random().toString(36).slice(2);

    return React.createElement(
      View,
      { style: { marginVertical: 4 } },
      label && React.createElement(
        Text,
        { style: { fontSize: 14, color: '#6b7280', marginBottom: 4 } },
        label
      ),
      React.createElement(
        TextInput,
        {
          value: value,
          placeholder: placeholder,
          onChangeText: onChangeText,
          editable: !disabled,
          style: this.getNativeStyles(),
          ...otherProps
        }
      ),
      error && React.createElement(
        Text,
        { style: { fontSize: 12, color: '#ef4444', marginTop: 4 } },
        error
      )
    );
  }
}