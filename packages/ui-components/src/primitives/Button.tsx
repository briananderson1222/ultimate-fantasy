import React from "react";
import { VariantProps } from "class-variance-authority";
import { UIComponent, UIComponentProps } from "../models/UIComponent";
import { PlatformAdapter } from "../adapters/platform";

export interface ButtonVariants {
  variant: "primary" | "secondary" | "ghost";
  size: "sm" | "md" | "lg";
}

export interface ButtonProps extends UIComponentProps, VariantProps<any> {
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onPress?: () => void;
  disabled?: boolean;
  children: React.ReactNode;
  variant?: ButtonVariants["variant"];
  size?: ButtonVariants["size"];
}

export class Button extends UIComponent<ButtonProps> {
  static defaultProps = {
    variant: "primary" as const,
    size: "md" as const,
    loading: false,
    disabled: false,
  };

  getWebStyles() {
    const { variant = "primary", size = "md" } = this.props;

    const baseStyles = "inline-flex items-center justify-center rounded-[var(--radius-md)] font-medium transition-all duration-[var(--anim-duration-xs)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)] disabled:opacity-60 disabled:cursor-not-allowed press-scale hover-lift";

    const variantStyles = {
      primary: "bg-[var(--color-primary)] text-[var(--color-primary-contrast)] hover:opacity-90 active:opacity-95",
      secondary: "bg-[var(--color-secondary)] text-[var(--color-secondary-contrast)] hover:opacity-90 active:opacity-95",
      ghost: "bg-transparent text-[var(--color-text)] hover:bg-[rgba(0,0,0,0.04)] active:bg-[rgba(0,0,0,0.08)]",
    };

    const sizeStyles = {
      sm: "px-[var(--space-2)] py-[calc(var(--space-1))] text-sm",
      md: "px-[var(--space-3)] py-[var(--space-2)] text-sm",
      lg: "px-[var(--space-4)] py-[var(--space-3)] text-base",
    };

    return `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]}`;
  }

  getNativeStyles() {
    const { variant = "primary", size = "md" } = this.props;

    const baseStyles = {
      flexDirection: "row" as const,
      alignItems: "center",
      justifyContent: "center",
      borderRadius: 8,
      fontWeight: "500" as const,
    };

    const variantStyles = {
      primary: {
        backgroundColor: "#3b82f6",
        color: "#ffffff",
      },
      secondary: {
        backgroundColor: "#6b7280",
        color: "#ffffff",
      },
      ghost: {
        backgroundColor: "transparent",
        color: "#374151",
      },
    };

    const sizeStyles = {
      sm: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        fontSize: 14,
      },
      md: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        fontSize: 14,
      },
      lg: {
        paddingHorizontal: 16,
        paddingVertical: 12,
        fontSize: 16,
      },
    };

    return {
      ...baseStyles,
      ...variantStyles[variant],
      ...sizeStyles[size],
    };
  }

  render() {
    const { loading, leftIcon, rightIcon, children, onPress, disabled, className, ...otherProps } = this.props;

    if (PlatformAdapter.getCurrentPlatform() === "web") {
      const Spinner = loading ? (
        <span
          aria-hidden
          className={`mr-2 inline-block h-4 w-4 loading-spinner rounded-full border-2 ${
            this.props.variant === "primary"
              ? "[border-color:rgba(255,255,255,0.3)] border-t-[var(--color-primary-contrast)]"
              : "[border-color:rgba(0,0,0,0.2)] border-t-[var(--color-text)]"
          }`}
        />
      ) : null;

      return (
        <button
          className={`${this.getWebStyles()} ${className || ""}`}
          aria-busy={loading || undefined}
          disabled={disabled || loading}
          onClick={onPress}
          {...otherProps}
        >
          {loading ? (
            <>
              {Spinner}
              {children}
            </>
          ) : (
            <>
              {leftIcon && <span className="mr-2">{leftIcon}</span>}
              {children}
              {rightIcon && <span className="ml-2">{rightIcon}</span>}
            </>
          )}
        </button>
      );
    }

    // React Native implementation
    const React = require('react');
    const { TouchableOpacity, Text, ActivityIndicator, View } = require('react-native');

    const Spinner = loading ? (
      React.createElement(ActivityIndicator, {
        size: 'small',
        color: this.props.variant === 'primary' ? '#ffffff' : '#374151',
        style: { marginRight: 8 }
      })
    ) : null;

    return React.createElement(
      TouchableOpacity,
      {
        style: [this.getNativeStyles(), disabled && { opacity: 0.6 }],
        onPress: onPress,
        disabled: disabled || loading,
        ...otherProps
      },
      React.createElement(
        View,
        { style: { flexDirection: 'row', alignItems: 'center' } },
        loading ? Spinner : leftIcon,
        React.createElement(Text, { style: { color: this.getNativeStyles().color } }, children),
        !loading && rightIcon
      )
    );
  }
}