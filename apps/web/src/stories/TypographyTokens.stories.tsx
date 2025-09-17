import type { Story } from '@ladle/react';
import { typographyTokens } from '../components/design-system/tokens/typography';

interface TypographySampleProps {
  label: string;
  style: React.CSSProperties;
  text?: string;
}

const TypographySample = ({ label, style, text = "The quick brown fox jumps over the lazy dog" }: TypographySampleProps) => (
  <div className="mb-6 p-4 border rounded-lg">
    <div className="text-sm font-mono text-gray-600 mb-2">{label}</div>
    <div style={style}>{text}</div>
    <div className="text-xs text-gray-500 mt-2 font-mono">
      Size: {style.fontSize} | Weight: {style.fontWeight} | Line Height: {style.lineHeight}
    </div>
  </div>
);

const TypographyShowcase = ({ scale }: { scale: 'mobile' | 'desktop' | 'base' }) => {
  const tokens = typographyTokens[scale];

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6 capitalize">{scale} Typography Scale</h2>

      <div className="space-y-1">
        <TypographySample
          label="Heading 1"
          style={tokens.h1}
          text="Main Page Heading"
        />

        <TypographySample
          label="Heading 2"
          style={tokens.h2}
          text="Section Heading"
        />

        <TypographySample
          label="Heading 3"
          style={tokens.h3}
          text="Subsection Heading"
        />

        <TypographySample
          label="Heading 4"
          style={tokens.h4}
          text="Card Title"
        />

        <TypographySample
          label="Body Large"
          style={tokens.bodyLarge}
          text="Large body text for emphasis. Perfect for introductory paragraphs or highlighted content that needs more visual weight."
        />

        <TypographySample
          label="Body"
          style={tokens.body}
          text="Regular body text for paragraphs and general content. This is the most commonly used text style for reading content."
        />

        <TypographySample
          label="Body Small"
          style={tokens.bodySmall}
          text="Small body text for secondary information, captions, or less important details."
        />

        <TypographySample
          label="Caption"
          style={tokens.caption}
          text="Caption text for images, metadata, or fine print information."
        />

        <TypographySample
          label="Button"
          style={tokens.button}
          text="BUTTON TEXT"
        />

        <TypographySample
          label="Label"
          style={tokens.label}
          text="Form Label"
        />
      </div>
    </div>
  );
};

const FontWeightDemo = () => {
  const weights = [300, 400, 500, 600, 700];

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Font Weight Scale</h2>

      <div className="space-y-4">
        {weights.map(weight => (
          <div key={weight} className="flex items-center space-x-4">
            <span className="w-16 text-sm font-mono text-gray-600">{weight}</span>
            <span style={{ fontWeight: weight, fontSize: '18px' }}>
              Fantasy Sports Design System
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const BaseScale: Story = () => <TypographyShowcase scale="base" />;

export const MobileScale: Story = () => <TypographyShowcase scale="mobile" />;

export const DesktopScale: Story = () => <TypographyShowcase scale="desktop" />;

export const FontWeights: Story = () => <FontWeightDemo />;

export const Comparison: Story = () => (
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <TypographyShowcase scale="mobile" />
    <TypographyShowcase scale="base" />
    <TypographyShowcase scale="desktop" />
  </div>
);

export const FantasyContent: Story = () => (
  <div className="p-6 max-w-2xl">
    <h1 style={typographyTokens.desktop.h1} className="mb-4">
      Ultimate Fantasy Football
    </h1>

    <h2 style={typographyTokens.desktop.h2} className="mb-3">
      Week 15 Matchups
    </h2>

    <p style={typographyTokens.base.bodyLarge} className="mb-4">
      Your team is projected to score 127.4 points this week with a 73% chance of winning.
    </p>

    <h3 style={typographyTokens.base.h3} className="mb-2">
      Starting Lineup
    </h3>

    <div className="space-y-2 mb-4">
      <div className="flex justify-between">
        <span style={typographyTokens.base.body}>Josh Allen (QB)</span>
        <span style={typographyTokens.base.bodySmall} className="text-green-600">23.2 pts</span>
      </div>
      <div className="flex justify-between">
        <span style={typographyTokens.base.body}>Christian McCaffrey (RB)</span>
        <span style={typographyTokens.base.bodySmall} className="text-green-600">18.7 pts</span>
      </div>
    </div>

    <p style={typographyTokens.base.bodySmall} className="text-gray-600">
      Projections updated 2 hours ago
    </p>
  </div>
);

BaseScale.meta = {
  title: 'Design System/Typography Tokens',
};