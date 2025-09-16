import { UIComponent } from '../../models/UIComponent';

describe('UIComponent Contract Tests', () => {
  describe('Component Props Validation', () => {
    it('should validate component name follows PascalCase', () => {
      // FAILING TEST - UIComponent model doesn't exist yet
      const validComponent = new UIComponent({
        name: 'Button',
        props: [],
        platforms: [
          { name: 'web', styling: 'tailwind', imports: [], adapters: [] }
        ]
      });

      expect(validComponent.name).toBe('Button');
    });

    it('should reject invalid component names', () => {
      // FAILING TEST - UIComponent model doesn't exist yet
      expect(() => {
        new UIComponent({
          name: 'invalidComponentName',
          props: [],
          platforms: []
        });
      }).toThrow('Component name must be PascalCase');
    });

    it('should validate component props structure', () => {
      // FAILING TEST - UIComponent model doesn't exist yet
      const component = new UIComponent({
        name: 'Button',
        props: [
          {
            name: 'variant',
            type: 'primary | secondary | danger',
            required: false,
            defaultValue: 'primary',
            description: 'Button visual variant'
          },
          {
            name: 'onClick',
            type: '() => void',
            required: true,
            description: 'Click handler function'
          }
        ],
        platforms: [
          { name: 'web', styling: 'tailwind', imports: [], adapters: [] }
        ]
      });

      expect(component.props).toHaveLength(2);
      expect(component.props[0].name).toBe('variant');
      expect(component.props[0].required).toBe(false);
      expect(component.props[1].required).toBe(true);
    });

    it('should validate prop names are valid JavaScript identifiers', () => {
      // FAILING TEST - UIComponent model doesn't exist yet
      expect(() => {
        new UIComponent({
          name: 'TestComponent',
          props: [
            {
              name: 'invalid-prop-name',
              type: 'string',
              required: false,
              description: 'Invalid prop'
            }
          ],
          platforms: []
        });
      }).toThrow('Property name must be a valid JavaScript identifier');
    });

    it('should validate platform configurations', () => {
      // FAILING TEST - UIComponent model doesn't exist yet
      const component = new UIComponent({
        name: 'Button',
        props: [],
        platforms: [
          {
            name: 'web',
            styling: 'tailwind',
            imports: ['react'],
            adapters: ['web-button-adapter']
          },
          {
            name: 'mobile',
            styling: 'stylesheet',
            imports: ['react-native'],
            adapters: ['mobile-button-adapter']
          }
        ]
      });

      expect(component.platforms).toHaveLength(2);
      expect(component.platforms[0].name).toBe('web');
      expect(component.platforms[1].name).toBe('mobile');
    });

    it('should reject invalid platform names', () => {
      // FAILING TEST - UIComponent model doesn't exist yet
      expect(() => {
        new UIComponent({
          name: 'Button',
          props: [],
          platforms: [
            {
              name: 'invalid' as any,
              styling: 'tailwind',
              imports: [],
              adapters: []
            }
          ]
        });
      }).toThrow(/Invalid enum value. Expected 'web' | 'mobile', received 'invalid'/);
    });

    it('should validate styling approach per platform', () => {
      // FAILING TEST - UIComponent model doesn't exist yet
      const webPlatform = {
        name: 'web' as const,
        styling: 'tailwind' as const,
        imports: [],
        adapters: []
      };

      const mobilePlatform = {
        name: 'mobile' as const,
        styling: 'stylesheet' as const,
        imports: [],
        adapters: []
      };

      const component = new UIComponent({
        name: 'Button',
        props: [],
        platforms: [webPlatform, mobilePlatform]
      });

      expect(component.platforms[0].styling).toBe('tailwind');
      expect(component.platforms[1].styling).toBe('stylesheet');
    });
  });
});