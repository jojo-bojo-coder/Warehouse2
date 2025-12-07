module.exports = {
  content: [
    './templates/**/*.html',
    './theme/templates/**/*.html',
    './*/templates/**/*.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
  // Add this for production optimization
  corePlugins: {
    preflight: true,
  }
}