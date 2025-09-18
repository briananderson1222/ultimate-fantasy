import React, { useEffect } from "react";
import { UIComponentProps } from "../models/UIComponent";
import { PlatformAdapter } from "../adapters/platform";

export interface ModalProps extends UIComponentProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

function getWebStyles() {
  return {
    overlay: "fixed inset-0 z-50 bg-[var(--color-overlay)]",
    content: "fixed left-1/2 top-1/2 z-50 w-[95vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-[var(--radius-md)] bg-[var(--color-surface)] p-4 shadow-lg outline-none",
    title: "mb-2 text-lg font-medium",
    close: "absolute right-2 top-2 rounded-[var(--radius-sm)] px-2 py-1 text-xs text-[var(--color-muted)] hover:bg-[rgba(0,0,0,0.04)] focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ring-offset)]",
  };
}

function getNativeStyles() {
  return {
    overlay: {
      position: "absolute" as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(0, 0, 0, 0.5)",
      zIndex: 50,
    },
    content: {
      position: "absolute" as const,
      top: "50%",
      left: "50%",
      transform: [{ translateX: -50 }, { translateY: -50 }],
      width: "95%",
      maxWidth: 400,
      backgroundColor: "#ffffff",
      borderRadius: 8,
      padding: 16,
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.25,
      shadowRadius: 8,
      elevation: 8,
    },
    title: {
      fontSize: 18,
      fontWeight: "500" as const,
      marginBottom: 8,
      color: "#374151",
    },
    close: {
      position: "absolute" as const,
      top: 8,
      right: 8,
      padding: 4,
      fontSize: 12,
      color: "#6b7280",
    },
  };
}

export const Modal: React.FC<ModalProps> = ({ open, onClose, title, children }) => {
  useEffect(() => {
    if (PlatformAdapter.getCurrentPlatform() === "web" && open) {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          onClose();
        }
      };
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [open, onClose]);

  if (!open) return null;

  if (PlatformAdapter.getCurrentPlatform() === "web") {
    const styles = getWebStyles();

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
        <div className={styles.overlay} onClick={onClose} />
        <div
          className={styles.content}
          style={{ color: "var(--color-text)", borderColor: "var(--border)" }}
        >
          <h2 className={title ? styles.title : "sr-only"}>
            {title || "Modal"}
          </h2>
          {children}
          <button
            aria-label="Close"
            className={styles.close}
            onClick={onClose}
          >
            Close (Esc)
          </button>
        </div>
      </div>
    );
  }

  // React Native implementation
  const React = require('react');
  const { Modal: RNModal, View, Text, TouchableOpacity, TouchableWithoutFeedback } = require('react-native');

  const styles = getNativeStyles();

  return React.createElement(
    RNModal,
    {
      visible: open,
      transparent: true,
      animationType: 'fade',
      onRequestClose: onClose,
    },
    React.createElement(
      TouchableWithoutFeedback,
      { onPress: onClose },
      React.createElement(
        View,
        { style: styles.overlay },
        React.createElement(
          TouchableWithoutFeedback,
          { onPress: (e: any) => e.stopPropagation() },
          React.createElement(
            View,
            { style: styles.content },
            React.createElement(
              Text,
              { style: styles.title },
              title || 'Modal'
            ),
            children,
            React.createElement(
              TouchableOpacity,
              {
                style: styles.close,
                onPress: onClose,
              },
              React.createElement(
                Text,
                { style: { fontSize: 12, color: '#6b7280' } },
                '✕'
              )
            )
          )
        )
      )
    )
  );
};