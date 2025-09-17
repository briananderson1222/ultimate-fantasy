import type { Story } from '@ladle/react';
import { colorTokens } from '../components/design-system/tokens/colors';

interface ColorSwatchProps {
  name: string;
  color: string;
  description?: string;
}

const ColorSwatch = ({ name, color, description }: ColorSwatchProps) => (
  <div className="flex flex-col items-center space-y-2">
    <div
      className="w-20 h-20 rounded-lg shadow-md border flex items-center justify-center"
      style={{ backgroundColor: color }}
    >
      {/* Show contrast text on light colors */}
      <span className="text-xs font-mono text-white mix-blend-difference">
        {color}
      </span>
    </div>
    <div className="text-center">
      <div className="font-semibold text-sm">{name}</div>
      {description && (
        <div className="text-xs text-gray-600">{description}</div>
      )}
    </div>
  </div>
);

const ColorPalette = ({ theme }: { theme: 'light' | 'dark' }) => {
  const tokens = colorTokens[theme];

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">{theme === 'dark' ? 'Dark' : 'Light'} Theme Colors</h2>

      <div className="space-y-8">
        <section>
          <h3 className="text-lg font-semibold mb-4">Semantic Colors</h3>
          <div className="grid grid-cols-4 gap-6">
            <ColorSwatch
              name="Primary"
              color={tokens.primary}
              description="Main accent color"
            />
            <ColorSwatch
              name="Success"
              color={tokens.success}
              description="Positive actions"
            />
            <ColorSwatch
              name="Warning"
              color={tokens.warning}
              description="Alerts and warnings"
            />
            <ColorSwatch
              name="Surface"
              color={tokens.surface}
              description="Card backgrounds"
            />
          </div>
        </section>

        <section>
          <h3 className="text-lg font-semibold mb-4">Background & Text</h3>
          <div className="grid grid-cols-3 gap-6">
            <ColorSwatch
              name="Background"
              color={tokens.background.from}
              description="Main background start"
            />
            <ColorSwatch
              name="Text Primary"
              color={tokens.textPrimary}
              description="Main text color"
            />
            <ColorSwatch
              name="Text Secondary"
              color={tokens.textSecondary}
              description="Secondary text"
            />
          </div>
        </section>

        <section>
          <h3 className="text-lg font-semibold mb-4">Border</h3>
          <div className="grid grid-cols-1 gap-6">
            <ColorSwatch
              name="Border"
              color={tokens.border}
              description="Component borders"
            />
          </div>
        </section>

        <section>
          <h3 className="text-lg font-semibold mb-4">Gradient Example</h3>
          <div
            className="h-24 rounded-lg flex items-center justify-center text-white font-semibold"
            style={{
              background: `linear-gradient(${tokens.background.direction || 'to-b'}, ${tokens.background.from}, ${tokens.background.to})`
            }}
          >
            Background Gradient
          </div>
        </section>
      </div>
    </div>
  );
};

export const DarkTheme: Story = () => <ColorPalette theme="dark" />;

export const LightTheme: Story = () => <ColorPalette theme="light" />;

export const Comparison: Story = () => (
  <div className="grid grid-cols-2 gap-8">
    <ColorPalette theme="dark" />
    <ColorPalette theme="light" />
  </div>
);

DarkTheme.meta = {
  title: 'Design System/Color Tokens',
};