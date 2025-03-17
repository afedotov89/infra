# Frontend Project

This project is built using Next.js with React and Material UI. It provides a solid foundation for a scalable web application with a professional structure.

## Project Structure

```
frontend/
├── package.json          # Node.js project manifest with dependencies and scripts for Next.js, React, and Material UI.
├── next.config.js        # Next.js configuration file.
├── .eslintrc.json        # ESLint configuration specific to Next.js.
├── pages/                # Next.js pages directory.
│   ├── _app.js           # Custom App component to integrate Material UI and global configurations.
│   ├── index.js          # Sample homepage demonstrating usage of Material UI components.
│   └── settings.js       # Settings page with theme mode configuration.
├── src/                  # Source code directory.
│   ├── theme.js          # Material UI theme customization.
│   ├── contexts/         # React contexts for state management.
│   │   └── ThemeContext.js # Theme context for managing application theme settings.
│   └── components/       # Directory for reusable React components.
│       └── Header.js     # Header component with theme indicator and navigation.
├── public/               # Static assets like images, fonts, etc.
└── README.md             # This README file.
```

## Common Components

The project includes a set of common reusable components located in the folder `src/components/`. These components are designed to promote consistency and reusability across the application. For example:

- **Header**: A modern, minimal header component that displays the application name "LangTask AI" and is rendered on all pages.

## Features

- **Theme Switching**: The application supports light, dark, and system themes. Users can change the theme from the settings page.
- **Responsive Design**: Built with Material UI components for a responsive and mobile-friendly interface.
- **Theme Persistence**: User's theme preference is saved to localStorage and persists between sessions.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Run the development server:
   ```bash
   npm run dev
   ```
3. Open [http://localhost:3000](http://localhost:3000) in your browser to view the application.

## Available Scripts

- `npm run dev`   - Runs the application in development mode.
- `npm run build` - Builds the application for production.
- `npm run start` - Starts the production server.
- `npm run lint`  - Lints the codebase using ESLint.

## Additional Notes

- The project leverages Next.js for efficient server-side rendering and routing.
- Material UI is used to create a responsive and modern user interface.
- ESLint is configured with Next.js core web vitals to maintain code quality and consistency.