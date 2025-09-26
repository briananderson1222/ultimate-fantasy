import React from "react";
import { colorTokens } from "./colors";

export default { title: "Design System/Tokens/Colors" };

export const AllColors = () => {
  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">Color Tokens</h2>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Dark Theme Colors</h3>
        <div className="grid grid-cols-4 gap-4">
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.dark.primary }}
            />
            <div className="text-xs">
              <div className="font-mono">Primary</div>
              <div className="text-gray-600">{colorTokens.dark.primary}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.dark.success }}
            />
            <div className="text-xs">
              <div className="font-mono">Success</div>
              <div className="text-gray-600">{colorTokens.dark.success}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.dark.warning }}
            />
            <div className="text-xs">
              <div className="font-mono">Warning</div>
              <div className="text-gray-600">{colorTokens.dark.warning}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.dark.surface }}
            />
            <div className="text-xs">
              <div className="font-mono">Surface</div>
              <div className="text-gray-600">{colorTokens.dark.surface}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Light Theme Colors</h3>
        <div className="grid grid-cols-4 gap-4">
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.light.primary }}
            />
            <div className="text-xs">
              <div className="font-mono">Primary</div>
              <div className="text-gray-600">{colorTokens.light.primary}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.light.success }}
            />
            <div className="text-xs">
              <div className="font-mono">Success</div>
              <div className="text-gray-600">{colorTokens.light.success}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.light.warning }}
            />
            <div className="text-xs">
              <div className="font-mono">Warning</div>
              <div className="text-gray-600">{colorTokens.light.warning}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div
              className="w-20 h-20 rounded border border-gray-300"
              style={{ backgroundColor: colorTokens.light.surface }}
            />
            <div className="text-xs">
              <div className="font-mono">Surface</div>
              <div className="text-gray-600">{colorTokens.light.surface}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const PrimaryColors = () => (
  <div className="p-4 space-y-4">
    <h3 className="text-lg font-semibold">Primary Colors</h3>
    <div className="grid grid-cols-2 gap-4">
      <div className="text-center">
        <div
          className="w-20 h-20 rounded mx-auto mb-2"
          style={{ backgroundColor: colorTokens.dark.primary }}
        />
        <div className="text-sm font-mono">Dark Primary</div>
        <div className="text-xs text-gray-600">{colorTokens.dark.primary}</div>
      </div>
      <div className="text-center">
        <div
          className="w-20 h-20 rounded mx-auto mb-2"
          style={{ backgroundColor: colorTokens.light.primary }}
        />
        <div className="text-sm font-mono">Light Primary</div>
        <div className="text-xs text-gray-600">{colorTokens.light.primary}</div>
      </div>
    </div>
  </div>
);

export const SemanticColors = () => (
  <div className="p-4 space-y-4">
    <h3 className="text-lg font-semibold">Semantic Colors</h3>
    <div className="grid grid-cols-2 gap-4">
      <div className="text-center">
        <div
          className="w-16 h-16 rounded mx-auto mb-2"
          style={{ backgroundColor: colorTokens.dark.success }}
        />
        <div className="text-sm">Success (Dark)</div>
      </div>
      <div className="text-center">
        <div
          className="w-16 h-16 rounded mx-auto mb-2"
          style={{ backgroundColor: colorTokens.dark.warning }}
        />
        <div className="text-sm">Warning (Dark)</div>
      </div>
    </div>
  </div>
);
