# Running Kivy in Docker

Running a Graphical User Interface (GUI) application like Kivy inside Docker requires granting the container access to your host machine's display and input devices.

## 1. Prerequisites

Ensure your Docker image is built with the necessary dependencies (SDL2, OpenGL, etc.). The provided `Dockerfile` has been updated to include these.

## 2. Running on Linux / Raspberry Pi (Native)

This is the most common scenario for deployment. You need to forward the X11 socket and hardware permissions.

### Option A: Using `docker run`

```bash
docker run -it --rm \
  --env="DISPLAY" \
  --env="QT_X11_NO_MITSHM=1" \
  --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  --device=/dev/dri:/dev/dri \
  --device=/dev/vchiq:/dev/vchiq \
  --network=host \
  neuropi-app python main.py
```

*   `--env="DISPLAY"`: passes the display ID (usually `:0`).
*   `--volume="/tmp/.X11-unix..."`: shares the X window system socket.
*   `--device=/dev/dri`: gives access to the GPU (Direct Rendering Infrastructure).
*   `--device=/dev/vchiq`: specific to Raspberry Pi GPU access.

### Option B: Using Docker Compose

Add a new service or update the existing one in `docker-compose.yml`:

```yaml
services:
  neuropi-gui:
    build: .
    environment:
      - DISPLAY=${DISPLAY}
      - QT_X11_NO_MITSHM=1
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
    devices:
      - /dev/dri:/dev/dri
      - /dev/vchiq:/dev/vchiq  # RPi only
    command: python main.py
```

**Note for Raspberry Pi**: You might need to run `xhost +local:root` on the host machine before starting the container to allow permissions.

## 3. Running on Windows (Docker Desktop + WSL 2)

Windows 11 (and updated Windows 10) supports **WSLg**, which allows running Linux GUI apps directly.

1.  **Ensure WSL 2 is installed** and updated.
2.  **Drivers**: Use vGPU enabled drivers for Docker Desktop.
3.  **Run Command**:

```bash
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /mnt/wslg:/mnt/wslg \
  -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
  -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
  -e PULSE_SERVER=$PULSE_SERVER \
  neuropi-app python main.py
```

(Note: You may need to replace `python main.py` with whatever command starts your app).

## 4. No Display (Headless)?

Kivy applications **cannot run** without a display. If you see errors like `[CRITICAL] [Window      ] Unable to find any valuable Window provider`, it means the container cannot see a screen.

## 5. Camera Access

Since your app uses the camera, you **MUST** pass the camera device to the container:

```bash
docker run ... --device=/dev/video0:/dev/video0 ...
```

Or in Compose:

```yaml
    devices:
      - /dev/video0:/dev/video0
```
