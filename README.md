# 🦅 IPL Auction Simulator (Backend)

The robust **Django** backend that powers the IPL Auction Simulator. It manages the auction state, handles real-time syncing (via polling), and houses the **Black-Box AI** that determines the winner.

## ⚙️ Core Functionality

### 1. Auction Management API
-   **Room State**: Manages bidding, timers, and player transitions.
-   **Bidding Logic**: Validates budgets, increments bids dynamically (e.g., +20L for high bids).
-   **Concurrency**: Handles multiple users (Host + Bidders) synchronized via a central Room state.

### 2. The Black-Box AI Engine (`auction/services/`)
This is the heart of the winner declaration system.
-   **`ppi_calculator.py`**: Assigns a **hidden strength score** (PPI) to every player based on:
    -   Base Price (Higher price = likely better player)
    -   Role (All-rounders often rated higher)
    -   Random Potential Factor (Simulates form/consistency)
-   **`team_evaluator.py`**: Algorithms that analyze a submitted Playing XI:
    -   Calculates total team strength.
    -   Applies **Penalties** for poor squad composition (No Wicket Keeper, Weak Bowling).
    -   Enforces rules (Max 4 Overseas players).

## 📂 Project Structure
-   `auction/models.py`: Database schema for Players, Teams, Rooms, and Bids.
-   `auction/views.py`: API endpoints for the frontend.
-   `auction/services/`: The business logic for AI evaluation.

## 🚀 How to Run

1.  **Install Requirements** (Ensure Python is installed):
    ```bash
    pip install django djangorestframework django-cors-headers pandas
    ```
2.  **Apply Migrations**:
    ```bash
    python manage.py migrate
    ```
3.  **Import Players** (Populate DB from Excel):
    ```bash
    python import_players_final.py
    ```
4.  **Start Server**:
    ```bash
    python manage.py runserver
    ```

## 🛠️ Tech Stack
-   **Django & DRF** (Backend Framework)
-   **SQLite** (Database)
-   **Pandas** (Data Processing for Excel imports)
