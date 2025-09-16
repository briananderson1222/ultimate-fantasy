import React from "react";
import { UIComponent, UIComponentProps } from "../models/UIComponent";
import { PlatformAdapter } from "../adapters/platform";

export interface CardProps extends UIComponentProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardHeaderProps extends UIComponentProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardTitleProps extends UIComponentProps {
  children: React.ReactNode;
  className?: string;
}

export class Card extends UIComponent<CardProps> {
  getWebStyles() {
    const { className } = this.props;
    return `rounded-[var(--radius-md)] border bg-[var(--color-surface)] p-4 shadow-sm transition-shadow hover:shadow-md ${className || ""}`.trim();
  }

  getNativeStyles() {
    return {
      borderRadius: 8,
      backgroundColor: "#ffffff",
      padding: 16,
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
      elevation: 2,
      borderWidth: 1,
      borderColor: "#e5e7eb",
    };
  }

  render() {
    const { children, className, ...otherProps } = this.props;

    if (PlatformAdapter.getCurrentPlatform() === "web") {
      return (
        <div
          className={this.getWebStyles()}
          style={{ borderColor: "var(--border)", color: "var(--color-text)" }}
          {...otherProps}
        >
          {children}
        </div>
      );
    }

    // React Native implementation
    const React = require('react');
    const { View } = require('react-native');

    return React.createElement(
      View,
      {
        style: this.getNativeStyles(),
        ...otherProps
      },
      children
    );
  }
}

export class CardHeader extends UIComponent<CardHeaderProps> {
  getWebStyles() {
    const { className } = this.props;
    return `mb-2 flex items-center justify-between ${className || ""}`;
  }

  getNativeStyles() {
    return {
      marginBottom: 8,
      flexDirection: "row" as const,
      alignItems: "center",
      justifyContent: "space-between",
    };
  }

  render() {
    const { children, className, ...otherProps } = this.props;

    if (PlatformAdapter.getCurrentPlatform() === "web") {
      return (
        <div className={this.getWebStyles()} {...otherProps}>
          {children}
        </div>
      );
    }

    // React Native implementation
    const React = require('react');
    const { View } = require('react-native');

    return React.createElement(
      View,
      {
        style: this.getNativeStyles(),
        ...otherProps
      },
      children
    );
  }
}

export class CardTitle extends UIComponent<CardTitleProps> {
  getWebStyles() {
    const { className } = this.props;
    return `font-medium ${className || ""}`;
  }

  getNativeStyles() {
    return {
      fontWeight: "500" as const,
      fontSize: 16,
      color: "#374151",
    };
  }

  render() {
    const { children, className, ...otherProps } = this.props;

    if (PlatformAdapter.getCurrentPlatform() === "web") {
      return (
        <h2 className={this.getWebStyles()} {...otherProps}>
          {children}
        </h2>
      );
    }

    // React Native implementation
    const React = require('react');
    const { Text } = require('react-native');

    return React.createElement(
      Text,
      {
        style: this.getNativeStyles(),
        ...otherProps
      },
      children
    );
  }
}