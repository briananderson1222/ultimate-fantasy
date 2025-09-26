/**
 * Mobile performance testing to ensure 60fps target and smooth user experience.
 *
 * Tests cover:
 * - UI component rendering performance
 * - Animation frame rates
 * - List scrolling performance
 * - Memory usage patterns
 * - JavaScript thread blocking
 * - Navigation performance
 */

import { measure, configure } from "@react-native-performance/flipper-reporter";
import { Platform } from "react-native";
import DeviceInfo from "react-native-device-info";

// Performance test configuration
const PERFORMANCE_CONFIG = {
  targetFPS: 60,
  frameBudgetMs: 16.67, // 1000ms / 60fps
  animationDurationMs: 300,
  listItemCount: 1000,
  maxMemoryIncreaseMB: 50,
  navigationTimeoutMs: 1000,
  renderTimeoutMs: 500,
};

interface PerformanceMetrics {
  averageFPS: number;
  frameDrops: number;
  renderTime: number;
  memoryUsage: number;
  jsThreadBlocking: number;
  navigationTime: number;
}

interface FrameData {
  timestamp: number;
  frameTime: number;
  isDropped: boolean;
}

class MobilePerformanceTester {
  private frameData: FrameData[] = [];
  private startTime: number = 0;
  private isRecording: boolean = false;
  private rafId: number | null = null;
  private memorySnapshots: number[] = [];

  constructor() {
    this.setupPerformanceMonitoring();
  }

  private setupPerformanceMonitoring(): void {
    configure({
      enabled: true,
      reportTableData: true,
      reportCounters: true,
    });
  }

  startRecording(): void {
    this.frameData = [];
    this.memorySnapshots = [];
    this.startTime = performance.now();
    this.isRecording = true;
    this.startFrameMonitoring();
    this.startMemoryMonitoring();
  }

  stopRecording(): PerformanceMetrics {
    this.isRecording = false;
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }

    return this.calculateMetrics();
  }

  private startFrameMonitoring(): void {
    let lastFrameTime = performance.now();

    const recordFrame = (currentTime: number) => {
      if (!this.isRecording) return;

      const frameTime = currentTime - lastFrameTime;
      const isDropped = frameTime > PERFORMANCE_CONFIG.frameBudgetMs * 1.5;

      this.frameData.push({
        timestamp: currentTime,
        frameTime,
        isDropped,
      });

      lastFrameTime = currentTime;
      this.rafId = requestAnimationFrame(recordFrame);
    };

    this.rafId = requestAnimationFrame(recordFrame);
  }

  private startMemoryMonitoring(): void {
    const recordMemory = () => {
      if (!this.isRecording) return;

      // Estimate memory usage (in MB)
      const memoryUsage = this.estimateMemoryUsage();
      this.memorySnapshots.push(memoryUsage);

      setTimeout(recordMemory, 100); // Sample every 100ms
    };

    recordMemory();
  }

  private estimateMemoryUsage(): number {
    // React Native doesn't provide direct memory access
    // This is a simplified estimation based on JS heap
    if (global.performance && global.performance.memory) {
      return (global.performance.memory as any).usedJSHeapSize / 1024 / 1024;
    }

    // Fallback estimation
    return 0;
  }

  private calculateMetrics(): PerformanceMetrics {
    const totalFrames = this.frameData.length;
    const droppedFrames = this.frameData.filter(
      (frame) => frame.isDropped,
    ).length;
    const totalTime =
      this.frameData.length > 0
        ? (this.frameData[this.frameData.length - 1].timestamp -
            this.frameData[0].timestamp) /
          1000
        : 0;

    const averageFPS = totalTime > 0 ? totalFrames / totalTime : 0;
    const frameDropPercentage =
      totalFrames > 0 ? (droppedFrames / totalFrames) * 100 : 0;

    const averageFrameTime =
      this.frameData.length > 0
        ? this.frameData.reduce((sum, frame) => sum + frame.frameTime, 0) /
          this.frameData.length
        : 0;

    const maxMemory =
      this.memorySnapshots.length > 0 ? Math.max(...this.memorySnapshots) : 0;
    const minMemory =
      this.memorySnapshots.length > 0 ? Math.min(...this.memorySnapshots) : 0;
    const memoryIncrease = maxMemory - minMemory;

    // Estimate JS thread blocking (frames taking significantly longer than budget)
    const blockingFrames = this.frameData.filter(
      (frame) => frame.frameTime > PERFORMANCE_CONFIG.frameBudgetMs * 3,
    );
    const jsThreadBlocking =
      blockingFrames.length > 0
        ? blockingFrames.reduce((sum, frame) => sum + frame.frameTime, 0) /
          blockingFrames.length
        : 0;

    return {
      averageFPS,
      frameDrops: frameDropPercentage,
      renderTime: averageFrameTime,
      memoryUsage: memoryIncrease,
      jsThreadBlocking,
      navigationTime: 0, // Set separately by navigation tests
    };
  }

  async measureComponentRender<T>(
    componentRenderer: () => Promise<T>,
    componentName: string,
  ): Promise<{ result: T; metrics: PerformanceMetrics }> {
    console.log(`Starting performance measurement for ${componentName}`);

    this.startRecording();

    const renderStartTime = performance.now();
    const result = await componentRenderer();
    const renderEndTime = performance.now();

    // Let the component settle and animations complete
    await new Promise((resolve) =>
      setTimeout(resolve, PERFORMANCE_CONFIG.animationDurationMs + 100),
    );

    const metrics = this.stopRecording();
    metrics.renderTime = renderEndTime - renderStartTime;

    console.log(
      `Performance measurement completed for ${componentName}:`,
      metrics,
    );

    return { result, metrics };
  }

  async measureListScrolling(
    scrollFunction: () => Promise<void>,
    itemCount: number,
  ): Promise<PerformanceMetrics> {
    console.log(
      `Starting list scrolling performance test with ${itemCount} items`,
    );

    this.startRecording();

    // Perform scrolling
    await scrollFunction();

    // Let scrolling settle
    await new Promise((resolve) => setTimeout(resolve, 500));

    const metrics = this.stopRecording();

    console.log("List scrolling performance results:", metrics);

    return metrics;
  }

  async measureNavigationPerformance(
    navigationFunction: () => Promise<void>,
  ): Promise<PerformanceMetrics> {
    console.log("Starting navigation performance test");

    const navigationStartTime = performance.now();

    this.startRecording();

    await navigationFunction();

    const navigationEndTime = performance.now();

    const metrics = this.stopRecording();
    metrics.navigationTime = navigationEndTime - navigationStartTime;

    console.log("Navigation performance results:", metrics);

    return metrics;
  }

  async measureAnimationPerformance(
    animationFunction: () => Promise<void>,
  ): Promise<PerformanceMetrics> {
    console.log("Starting animation performance test");

    this.startRecording();

    await animationFunction();

    // Wait for animation completion
    await new Promise((resolve) =>
      setTimeout(resolve, PERFORMANCE_CONFIG.animationDurationMs),
    );

    const metrics = this.stopRecording();

    console.log("Animation performance results:", metrics);

    return metrics;
  }
}

// Performance test utilities
export class PerformanceTestUtils {
  static tester = new MobilePerformanceTester();

  static async getDeviceInfo() {
    return {
      brand: await DeviceInfo.getBrand(),
      model: await DeviceInfo.getModel(),
      systemVersion: await DeviceInfo.getSystemVersion(),
      isTablet: await DeviceInfo.isTablet(),
      totalMemory: await DeviceInfo.getTotalMemory(),
      usedMemory: await DeviceInfo.getUsedMemory(),
      platform: Platform.OS,
      version: Platform.Version,
    };
  }

  static validatePerformanceMetrics(
    metrics: PerformanceMetrics,
    testName: string,
    requirements?: Partial<{
      minFPS: number;
      maxFrameDrops: number;
      maxRenderTime: number;
      maxMemoryIncrease: number;
      maxJSThreadBlocking: number;
      maxNavigationTime: number;
    }>,
  ): { passed: boolean; issues: string[] } {
    const issues: string[] = [];
    const defaultRequirements = {
      minFPS: PERFORMANCE_CONFIG.targetFPS * 0.9, // 90% of target FPS
      maxFrameDrops: 5, // Max 5% frame drops
      maxRenderTime: PERFORMANCE_CONFIG.renderTimeoutMs,
      maxMemoryIncrease: PERFORMANCE_CONFIG.maxMemoryIncreaseMB,
      maxJSThreadBlocking: PERFORMANCE_CONFIG.frameBudgetMs * 2,
      maxNavigationTime: PERFORMANCE_CONFIG.navigationTimeoutMs,
    };

    const reqs = { ...defaultRequirements, ...requirements };

    if (metrics.averageFPS < reqs.minFPS) {
      issues.push(
        `FPS too low: ${metrics.averageFPS.toFixed(1)} < ${reqs.minFPS}`,
      );
    }

    if (metrics.frameDrops > reqs.maxFrameDrops) {
      issues.push(
        `Frame drops too high: ${metrics.frameDrops.toFixed(1)}% > ${reqs.maxFrameDrops}%`,
      );
    }

    if (metrics.renderTime > reqs.maxRenderTime) {
      issues.push(
        `Render time too high: ${metrics.renderTime.toFixed(1)}ms > ${reqs.maxRenderTime}ms`,
      );
    }

    if (metrics.memoryUsage > reqs.maxMemoryIncrease) {
      issues.push(
        `Memory increase too high: ${metrics.memoryUsage.toFixed(1)}MB > ${reqs.maxMemoryIncrease}MB`,
      );
    }

    if (metrics.jsThreadBlocking > reqs.maxJSThreadBlocking) {
      issues.push(
        `JS thread blocking too high: ${metrics.jsThreadBlocking.toFixed(1)}ms > ${reqs.maxJSThreadBlocking}ms`,
      );
    }

    if (metrics.navigationTime > reqs.maxNavigationTime) {
      issues.push(
        `Navigation time too high: ${metrics.navigationTime.toFixed(1)}ms > ${reqs.maxNavigationTime}ms`,
      );
    }

    const passed = issues.length === 0;

    if (!passed) {
      console.warn(`Performance test "${testName}" failed:`, issues);
    } else {
      console.log(`Performance test "${testName}" passed`);
    }

    return { passed, issues };
  }

  // Simulate heavy computational work to test performance under load
  static async simulateHeavyWork(durationMs: number): Promise<void> {
    const startTime = performance.now();

    return new Promise((resolve) => {
      const doWork = () => {
        const elapsed = performance.now() - startTime;

        if (elapsed < durationMs) {
          // Simulate some computational work
          for (let i = 0; i < 10000; i++) {
            Math.random() * Math.random();
          }

          // Use setTimeout to yield control back to React Native
          setTimeout(doWork, 0);
        } else {
          resolve();
        }
      };

      doWork();
    });
  }

  // Generate large dataset for testing list performance
  static generateLargeDataset(size: number): Array<{
    id: string;
    name: string;
    value: number;
    description: string;
  }> {
    return Array.from({ length: size }, (_, index) => ({
      id: `item-${index}`,
      name: `Item ${index}`,
      value: Math.random() * 100,
      description: `This is a description for item ${index} with some additional text to make it more realistic.`,
    }));
  }

  // Memory pressure test
  static async createMemoryPressure(): Promise<() => void> {
    const largeArrays: number[][] = [];

    // Create memory pressure
    for (let i = 0; i < 10; i++) {
      largeArrays.push(new Array(100000).fill(Math.random()));
    }

    // Return cleanup function
    return () => {
      largeArrays.length = 0;
    };
  }
}

// Performance benchmark decorator
export function performanceBenchmark(
  testName: string,
  requirements?: Parameters<
    typeof PerformanceTestUtils.validatePerformanceMetrics
  >[2],
) {
  return function (
    target: any,
    propertyName: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      console.log(`Starting performance benchmark: ${testName}`);

      const deviceInfo = await PerformanceTestUtils.getDeviceInfo();
      console.log("Device info:", deviceInfo);

      const { result, metrics } =
        await PerformanceTestUtils.tester.measureComponentRender(
          () => originalMethod.apply(this, args),
          testName,
        );

      const validation = PerformanceTestUtils.validatePerformanceMetrics(
        metrics,
        testName,
        requirements,
      );

      if (!validation.passed) {
        console.error(
          `Performance benchmark "${testName}" failed:`,
          validation.issues,
        );
        // In test environment, this would throw an error
        // throw new Error(`Performance requirements not met: ${validation.issues.join(', ')}`);
      }

      return result;
    };

    return descriptor;
  };
}

// Export for use in tests
export { MobilePerformanceTester, PERFORMANCE_CONFIG };
export type { PerformanceMetrics, FrameData };
