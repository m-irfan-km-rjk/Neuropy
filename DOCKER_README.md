# Docker Setup for NeuroPi

This guide explains how to run the NeuroPi application using Docker. This is optimized for ARM-based devices like the **Raspberry Pi 3B+** (referred to as "Arduino 3B+" in your request, but "3B+" is a Raspberry Pi model).

## Prerequisites

1.  **Install Docker** on your Raspberry Pi:
    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker pi
    ```
    *Log out and log back in for the group changes to take effect.*

2.  **Install Docker Compose** (if not included in the generic install script):
    ```bash
    sudo apt-get install -y docker-compose-plugin
    ```
    Or use `docker compose` (v2) which is standard now.

## Running the Application

1.  Navigate to the project directory on your Pi.
2.  Build and start the container:
    ```bash
    docker compose up -d --build
    ```

3.  The application will be running at `http://localhost:5000`.

## Notes

-   **Database Persistence**: The SQLite database is stored in the `instance/` folder. This folder is mapped as a volume in `docker-compose.yml` so your data persists even if the container is restarted.
-   **Timezone**: The `docker-compose.yml` includes a `TZ` variable (default `Asia/Kolkata`) to ensure the scheduler uses the correct local time. Change this if you are in a different time zone.
-   **Kiosk Mode**: Docker runs the *server*. To see the interface on the Pi's screen, you still need to open the browser. You can use the existing `setup.sh` logic for the autostart part, but modify it to just launch the browser since Docker manages the server.

    Example `/home/pi/.config/lxsession/LXDE-pi/autostart` (if using the Pi desktop):
    ```
    @chromium-browser --noerrdialogs --kiosk --incognito http://localhost:5000
    ```
