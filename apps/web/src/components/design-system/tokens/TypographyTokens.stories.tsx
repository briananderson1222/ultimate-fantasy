import React from "react";
import { typographyTokens } from "./typography";

export default { title: "Design System/Tokens/Typography" };

export const FontSizes = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Typography Scale</h2>
    {Object.entries(typographyTokens.base).map(([element, style]) => (
      <div key={element} className="flex items-center gap-4">
        <div className="w-24 text-sm text-gray-600">{element}</div>
        <div
          className="flex-1"
          style={{
            fontSize: style.fontSize,
            fontWeight: style.fontWeight,
            lineHeight: style.lineHeight,
          }}
        >
          The quick brown fox jumps over the lazy dog
        </div>
        <div className="text-sm text-gray-500 font-mono">{style.fontSize}</div>
      </div>
    ))}
  </div>
);

export const FontWeights = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Font Weight Examples</h2>
    <div className="space-y-2">
      <div className="text-lg" style={{ fontWeight: 300 }}>
        Light (300): The quick brown fox jumps over the lazy dog
      </div>
      <div className="text-lg" style={{ fontWeight: 400 }}>
        Regular (400): The quick brown fox jumps over the lazy dog
      </div>
      <div className="text-lg" style={{ fontWeight: 500 }}>
        Medium (500): The quick brown fox jumps over the lazy dog
      </div>
      <div className="text-lg" style={{ fontWeight: 600 }}>
        Semibold (600): The quick brown fox jumps over the lazy dog
      </div>
      <div className="text-lg" style={{ fontWeight: 700 }}>
        Bold (700): The quick brown fox jumps over the lazy dog
      </div>
    </div>
  </div>
);

export const MobileTypography = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Mobile Typography Scale</h2>
    {Object.entries(typographyTokens.mobile).map(([element, style]) => (
      <div key={element} className="space-y-1">
        <div className="text-sm text-gray-600">{element}</div>
        <div
          style={{
            fontSize: style.fontSize,
            fontWeight: style.fontWeight,
            lineHeight: style.lineHeight,
          }}
        >
          {element === "h1" && "Main Heading"}
          {element === "h2" && "Section Heading"}
          {element === "h3" && "Subsection Heading"}
          {element === "body" && "Body text for reading"}
          {element === "caption" && "Caption text"}
          {element === "button" && "Button Text"}
          {element === "label" && "Label Text"}
          {element.includes("body") && !element.includes("Large") && "Body text content"}
        </div>
      </div>
    ))}
  </div>
);

export const DesktopTypography = () => (
  <div className="p-6 space-y-4">
    <h2 className="text-2xl font-bold">Desktop Typography Scale</h2>
    {Object.entries(typographyTokens.desktop).map(([element, style]) => (
      <div key={element} className="space-y-1">
        <div className="text-sm text-gray-600">{element}</div>
        <div
          style={{
            fontSize: style.fontSize,
            fontWeight: style.fontWeight,
            lineHeight: style.lineHeight,
          }}
        >
          {element === "h1" && "Main Heading"}
          {element === "h2" && "Section Heading"}
          {element === "h3" && "Subsection Heading"}
          {element === "body" && "Body text for reading"}
          {element === "caption" && "Caption text"}
          {element === "button" && "Button Text"}
          {element === "label" && "Label Text"}
          {element.includes("body") && !element.includes("Large") && "Body text content"}
        </div>
      </div>
    ))}
  </div>
);

export const TypographyHierarchy = () => (
  <div className="p-6 space-y-4">
    <div className="text-4xl font-bold">Heading 1</div>
    <div className="text-3xl font-bold">Heading 2</div>
    <div className="text-2xl font-semibold">Heading 3</div>
    <div className="text-xl font-semibold">Heading 4</div>
    <div className="text-lg font-medium">Heading 5</div>
    <div className="text-base font-medium">Heading 6</div>
    <div className="text-base">Body Text Regular</div>
    <div className="text-base font-medium">Body Text Medium</div>
    <div className="text-sm">Small Text</div>
    <div className="text-xs">Caption Text</div>
    <div className="text-xs font-mono">Code Text</div>
  </div>
);
