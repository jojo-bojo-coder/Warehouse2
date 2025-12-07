module.exports = {
  content: [
    './templates/**/*.html',
    './theme/templates/**/*.html',
    './*/templates/**/*.html',
    './sportclub/templates/**/*.html',
    './pages/templates/**/*.html',
    './students/templates/**/*.html',
    './coach_dashboard/templates/**/*.html',
    './accounts/templates/**/*.html',
    './admin_dashboard/templates/**/*.html',
    './club_dashboard/templates/**/*.html',
    './accountant_dashboard/templates/**/*.html',
    './receptionist_dashboard/templates/**/*.html',
    './messenger/templates/**/*.html',
  ],
  theme: {
    extend: {
      fontFamily: {
        cairo: ['Cairo', 'sans-serif'],
      },
    },
  },
  plugins: [],
}