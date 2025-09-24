/**
 * CDN integration utilities for static asset optimization.
 *
 * This module provides functionality for:
 * - Asset URL generation with CDN endpoints
 * - Cache busting and versioning
 * - Optimized image delivery
 * - Static asset preloading
 */

import { env } from 'process';

interface CDNConfig {
  baseUrl: string;
  enableCache: boolean;
  defaultTTL: number;
  regions: string[];
  imageOptimization: {
    formats: string[];
    qualities: number[];
    sizes: number[];
  };
}

interface AssetOptions {
  version?: string;
  format?: 'webp' | 'avif' | 'jpg' | 'png';
  quality?: number;
  width?: number;
  height?: number;
  blur?: boolean;
  cache?: boolean;
}

class CDNManager {
  private config: CDNConfig;
  private assetCache = new Map<string, string>();

  constructor(config: CDNConfig) {
    this.config = config;
  }

  /**
   * Generate optimized CDN URL for an asset.
   */
  getAssetUrl(path: string, options: AssetOptions = {}): string {
    const cacheKey = `${path}-${JSON.stringify(options)}`;

    if (this.config.enableCache && this.assetCache.has(cacheKey)) {
      return this.assetCache.get(cacheKey)!;
    }

    let url = `${this.config.baseUrl}${path}`;

    // Add version for cache busting
    if (options.version) {
      url += `?v=${options.version}`;
    } else {
      // Use build hash or timestamp for cache busting
      const buildHash = env.NEXT_PUBLIC_BUILD_HASH || Date.now().toString();
      url += `?v=${buildHash}`;
    }

    // Add image optimization parameters
    if (this.isImageAsset(path)) {
      url = this.addImageOptimization(url, options);
    }

    if (this.config.enableCache) {
      this.assetCache.set(cacheKey, url);
    }

    return url;
  }

  /**
   * Generate responsive image URLs for different screen sizes.
   */
  getResponsiveImageUrls(path: string, options: AssetOptions = {}): Array<{ url: string; width: number }> {
    return this.config.imageOptimization.sizes.map(width => ({
      url: this.getAssetUrl(path, { ...options, width }),
      width
    }));
  }

  /**
   * Generate srcset for responsive images.
   */
  generateSrcSet(path: string, options: AssetOptions = {}): string {
    const urls = this.getResponsiveImageUrls(path, options);
    return urls.map(({ url, width }) => `${url} ${width}w`).join(', ');
  }

  /**
   * Preload critical assets for better performance.
   */
  preloadAssets(assets: Array<{ path: string; options?: AssetOptions; priority?: 'high' | 'low' }>): void {
    if (typeof document === 'undefined') return;

    assets.forEach(({ path, options = {}, priority = 'high' }) => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = this.getAssetUrl(path, options);

      if (this.isImageAsset(path)) {
        link.as = 'image';
      } else if (this.isStyleAsset(path)) {
        link.as = 'style';
      } else if (this.isScriptAsset(path)) {
        link.as = 'script';
      }

      if (priority === 'high') {
        link.setAttribute('fetchpriority', 'high');
      }

      document.head.appendChild(link);
    });
  }

  /**
   * Prefetch assets for future navigation.
   */
  prefetchAssets(assets: string[]): void {
    if (typeof document === 'undefined') return;

    assets.forEach(path => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = this.getAssetUrl(path);
      document.head.appendChild(link);
    });
  }

  /**
   * Get optimal image format based on browser support.
   */
  getOptimalImageFormat(): 'avif' | 'webp' | 'jpg' {
    if (typeof window === 'undefined') return 'jpg';

    // Check for AVIF support
    const canvas = document.createElement('canvas');
    if (canvas.toDataURL('image/avif').indexOf('data:image/avif') === 0) {
      return 'avif';
    }

    // Check for WebP support
    if (canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0) {
      return 'webp';
    }

    return 'jpg';
  }

  /**
   * Generate cache headers for static assets.
   */
  getCacheHeaders(path: string): Record<string, string> {
    const isVersioned = path.includes('v=') || path.includes('_next/static');

    if (isVersioned) {
      // Long-term caching for versioned assets
      return {
        'Cache-Control': 'public, max-age=31536000, immutable',
        'Expires': new Date(Date.now() + 31536000 * 1000).toUTCString()
      };
    }

    // Short-term caching for dynamic content
    return {
      'Cache-Control': `public, max-age=${this.config.defaultTTL}`,
      'Expires': new Date(Date.now() + this.config.defaultTTL * 1000).toUTCString()
    };
  }

  /**
   * Purge asset from CDN cache.
   */
  async purgeAsset(path: string): Promise<boolean> {
    try {
      const purgeUrl = `${this.config.baseUrl}/purge`;
      const response = await fetch(purgeUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paths: [path] })
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to purge asset from CDN:', error);
      return false;
    }
  }

  /**
   * Get CDN performance metrics.
   */
  async getPerformanceMetrics(): Promise<{
    hitRate: number;
    avgResponseTime: number;
    bandwidth: number;
    requestCount: number;
  }> {
    try {
      const response = await fetch(`${this.config.baseUrl}/metrics`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch CDN metrics:', error);
      return {
        hitRate: 0,
        avgResponseTime: 0,
        bandwidth: 0,
        requestCount: 0
      };
    }
  }

  private isImageAsset(path: string): boolean {
    return /\.(jpg|jpeg|png|gif|webp|avif|svg)$/i.test(path);
  }

  private isStyleAsset(path: string): boolean {
    return /\.css$/i.test(path);
  }

  private isScriptAsset(path: string): boolean {
    return /\.js$/i.test(path);
  }

  private addImageOptimization(url: string, options: AssetOptions): string {
    const params = new URLSearchParams();

    if (options.format) {
      params.append('format', options.format);
    }

    if (options.quality) {
      params.append('quality', options.quality.toString());
    }

    if (options.width) {
      params.append('width', options.width.toString());
    }

    if (options.height) {
      params.append('height', options.height.toString());
    }

    if (options.blur) {
      params.append('blur', '10');
    }

    if (params.toString()) {
      const separator = url.includes('?') ? '&' : '?';
      url += separator + params.toString();
    }

    return url;
  }
}

// Default CDN configuration
const defaultConfig: CDNConfig = {
  baseUrl: env.NEXT_PUBLIC_CDN_URL || 'https://cdn.ultimate-fantasy.com',
  enableCache: env.NODE_ENV === 'production',
  defaultTTL: 3600, // 1 hour
  regions: ['us-east-1', 'us-west-2', 'eu-west-1'],
  imageOptimization: {
    formats: ['avif', 'webp', 'jpg'],
    qualities: [50, 75, 90],
    sizes: [320, 640, 768, 1024, 1280, 1920]
  }
};

// Global CDN manager instance
export const cdnManager = new CDNManager(defaultConfig);

// Utility functions for common use cases
export const getAssetUrl = (path: string, options?: AssetOptions) =>
  cdnManager.getAssetUrl(path, options);

export const getImageSrcSet = (path: string, options?: AssetOptions) =>
  cdnManager.generateSrcSet(path, options);

export const preloadCriticalAssets = (assets: Array<{ path: string; options?: AssetOptions }>) =>
  cdnManager.preloadAssets(assets);

export const getOptimalImageFormat = () =>
  cdnManager.getOptimalImageFormat();

// React hook for CDN assets
export function useCDNAsset(path: string, options?: AssetOptions) {
  const url = cdnManager.getAssetUrl(path, options);
  const srcSet = cdnManager.generateSrcSet(path, options);

  return {
    url,
    srcSet,
    preload: () => cdnManager.preloadAssets([{ path, options }]),
    prefetch: () => cdnManager.prefetchAssets([path])
  };
}

// Image component props helper
export function getCDNImageProps(src: string, options?: AssetOptions & { alt: string }) {
  const { alt, ...assetOptions } = options || { alt: '' };

  return {
    src: cdnManager.getAssetUrl(src, assetOptions),
    srcSet: cdnManager.generateSrcSet(src, assetOptions),
    alt,
    loading: 'lazy' as const,
    decoding: 'async' as const,
    sizes: '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw'
  };
}

export type { CDNConfig, AssetOptions };
export { CDNManager };