/** @type {import('@ladle/react').Config} */
export default {
  // Pick up stories colocated with components
  stories: ["src/**/*.stories.@(tsx|ts)"],
  defaultStory: {
    controls: { disabled: false },
  },
};
