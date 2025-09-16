import { SharedPackage } from '../../models/SharedPackage';

describe('SharedPackage Contract Tests', () => {
  describe('Package Manifest Validation', () => {
    it('should validate package name follows npm conventions', () => {
      // FAILING TEST - SharedPackage model doesn't exist yet
      const validPackage = new SharedPackage({
        name: '@ultimate-fantasy/shared-logic',
        version: '1.0.0',
        platform: 'shared',
        dependencies: [],
        exports: []
      });

      expect(validPackage.name).toBe('@ultimate-fantasy/shared-logic');
    });

    it('should reject invalid package names', () => {
      expect(() => {
        new SharedPackage({
          name: 'Invalid Package Name',
          version: '1.0.0',
          platform: 'shared',
          dependencies: [],
          exports: []
        });
      }).toThrow(); // Just check that it throws, don't check specific message
    });

    it('should validate semantic versioning', () => {
      // FAILING TEST - SharedPackage model doesn't exist yet
      const validPackage = new SharedPackage({
        name: '@ultimate-fantasy/test',
        version: '1.2.3',
        platform: 'shared',
        dependencies: [],
        exports: []
      });

      expect(validPackage.version).toBe('1.2.3');
    });

    it('should reject invalid version formats', () => {
      expect(() => {
        new SharedPackage({
          name: '@ultimate-fantasy/test',
          version: 'invalid.version',
          platform: 'shared',
          dependencies: [],
          exports: []
        });
      }).toThrow(); // Just check that it throws, don't check specific message
    });

    it('should validate platform enum values', () => {
      // FAILING TEST - SharedPackage model doesn't exist yet
      const platforms: Array<'shared' | 'web' | 'mobile' | 'universal'> = [
        'shared', 'web', 'mobile', 'universal'
      ];

      platforms.forEach(platform => {
        const pkg = new SharedPackage({
          name: '@ultimate-fantasy/test',
          version: '1.0.0',
          platform,
          dependencies: [],
          exports: []
        });

        expect(pkg.platform).toBe(platform);
      });
    });

    it('should reject invalid platform values', () => {
      expect(() => {
        new SharedPackage({
          name: '@ultimate-fantasy/test',
          version: '1.0.0',
          platform: 'invalid' as any,
          dependencies: [],
          exports: []
        });
      }).toThrow(); // Just check that it throws, don't check specific message
    });

    it('should validate exports array structure', () => {
      // FAILING TEST - SharedPackage model doesn't exist yet
      const pkg = new SharedPackage({
        name: '@ultimate-fantasy/test',
        version: '1.0.0',
        platform: 'shared',
        dependencies: [],
        exports: [
          {
            name: 'testFunction',
            type: 'function',
            signature: '(input: string) => string',
            platform: 'universal',
            deprecated: false
          }
        ]
      });

      expect(pkg.exports).toHaveLength(1);
      expect(pkg.exports[0].name).toBe('testFunction');
    });
  });
});