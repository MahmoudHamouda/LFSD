# LFSD Frontend

The web client for the Life Operating System (LFSD), built with React, Vite, and TypeScript.

## Tech Stack
- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: CSS Modules / Vanilla CSS (Custom Token System)
- **State Management**: React Context / Hooks
- **Routing**: React Router

## Directory Structure
- `src/assets/`: Static assets (images, icons).
- `src/components/`: Reusable UI components (Buttons, Cards, Modals).
- `src/context/`: Global state contexts (AuthContext, etc.).
- `src/pages/`: Main application pages (Home, Login, Dashboard, Chat).
- `src/services/`: API clients and service layers.
- `src/types/`: TypeScript type definitions.
- `src/utils/`: Helper functions (formatting, validation).

## Setup & Running

1.  **Prerequisites**: Node.js 16+
2.  **Install Dependencies**:
    ```bash
    npm install
    ```

3.  **Environment Variables**:
    Create a `.env` file in the `frontend/` directory (if needed, usually Vite uses `.env.local`):
    ```env
    VITE_API_BASE_URL=http://localhost:8003
    ```

4.  **Run Development Server**:
    ```bash
    npm run dev
    ```
    The application will generally be available at [http://localhost:3000](http://localhost:3000).

5.  **Build for Production**:
    ```bash
    npm run build
    ```
    Output will be in the `dist/` directory.

## Key Screens
- **Dashboard**: High-level view of Life Score (VivIndex).
- **Chat**: Operational command center for talking to the AI assistant.
- **Finance**: Deep dive into financial pillars (Cashflow, Net Worth, Goals).
- **Health**: Health metrics and sleep data visualization.
- **Calendar**: Day/Week view of time blocks and productivity score.
