import React from "react";
import { ProgressBar } from "./ProgressBar";

export default { title: "Design System/Primitives/ProgressBar" };

export const Default = () => (
  <div className="p-6 space-y-4">
    <ProgressBar value={50} max={100} />
  </div>
);

export const DifferentValues = () => (
  <div className="p-6 space-y-4">
    <div className="space-y-2">
      <div className="text-sm">10%</div>
      <ProgressBar value={10} max={100} />
    </div>
    <div className="space-y-2">
      <div className="text-sm">35%</div>
      <ProgressBar value={35} max={100} />
    </div>
    <div className="space-y-2">
      <div className="text-sm">75%</div>
      <ProgressBar value={75} max={100} />
    </div>
    <div className="space-y-2">
      <div className="text-sm">100%</div>
      <ProgressBar value={100} max={100} />
    </div>
  </div>
);

export const WithLabels = () => (
  <div className="p-6 space-y-4">
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Win Percentage</span>
        <span>65%</span>
      </div>
      <ProgressBar value={65} max={100} />
    </div>
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Season Progress</span>
        <span>8/12 weeks</span>
      </div>
      <ProgressBar value={8} max={12} />
    </div>
  </div>
);

export const Sizes = () => (
  <div className="p-6 space-y-6">
    <div className="space-y-2">
      <div className="text-sm">Small</div>
      <ProgressBar value={60} max={100} size="sm" />
    </div>
    <div className="space-y-2">
      <div className="text-sm">Medium (Default)</div>
      <ProgressBar value={60} max={100} size="md" />
    </div>
    <div className="space-y-2">
      <div className="text-sm">Large</div>
      <ProgressBar value={60} max={100} size="lg" />
    </div>
  </div>
);

export const Colors = () => (
  <div className="p-6 space-y-4">
    <div className="space-y-2">
      <div className="text-sm">Primary (Default)</div>
      <ProgressBar value={60} max={100} />
    </div>
    <div className="space-y-2">
      <div className="text-sm">Success</div>
      <ProgressBar value={60} max={100} variant="success" />
    </div>
    <div className="space-y-2">
      <div className="text-sm">Warning</div>
      <ProgressBar value={60} max={100} variant="warning" />
    </div>
    <div className="space-y-2">
      <div className="text-sm">Error</div>
      <ProgressBar value={60} max={100} variant="error" />
    </div>
  </div>
);

export const FantasySports = () => (
  <div className="p-6 space-y-6">
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Playoff Chances</span>
        <span>78%</span>
      </div>
      <ProgressBar value={78} max={100} variant="success" />
    </div>
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Roster Completeness</span>
        <span>85%</span>
      </div>
      <ProgressBar value={85} max={100} />
    </div>
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Injury Risk</span>
        <span>25%</span>
      </div>
      <ProgressBar value={25} max={100} variant="warning" />
    </div>
  </div>
);