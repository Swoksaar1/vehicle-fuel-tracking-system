const { app, BrowserWindow } = require("electron");
const path = require("node:path");
const { spawn } = require("node:child_process");
const http = require("node:http");
const fs = require("node:fs");

const isDev = !app.isPackaged;

let mainWindow = null;
let backendProcess = null;

const FRONTEND_DEV_URL = "http://localhost:3000";
const FRONTEND_BUILD_FILE = path.join(__dirname, "../frontend/build/index.html");
const BACKEND_HEALTH_URL = "http://127.0.0.1:8000/api/dashboard-summary/";

function log(...args) {
  console.log("[electron]", ...args);
}

function logError(...args) {
  console.error("[electron error]", ...args);
}

function checkUrl(url, timeout = 2000) {
  return new Promise((resolve) => {
    log("Checking URL:", url);

    const req = http.get(url, (res) => {
      log("URL responded:", url, "status:", res.statusCode);
      res.resume();
      resolve(true);
    });

    req.on("error", (error) => {
      log("URL check failed:", url, error.message);
      resolve(false);
    });

    req.setTimeout(timeout, () => {
      log("URL timeout:", url);
      req.destroy();
      resolve(false);
    });
  });
}

function waitForBackend(url, timeout = 30000) {
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const check = async () => {
      const ok = await checkUrl(url, 2000);

      if (ok) {
        log("Backend is available:", url);
        resolve(true);
        return;
      }

      if (Date.now() - start > timeout) {
        reject(new Error(`Backend not available: ${url}`));
        return;
      }

      setTimeout(check, 500);
    };

    check();
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    if (backendProcess) {
      log("Backend already running.");
      resolve();
      return;
    }

    try {
      if (isDev) {
        const appPath = app.getAppPath();
        const pythonExe = path.join(appPath, "venv", "Scripts", "python.exe");
        const backendScript = path.join(appPath, "run.backend.py");

        log("Running in development mode");
        log("App path:", appPath);
        log("Python path:", pythonExe);
        log("Backend script:", backendScript);

        if (!fs.existsSync(pythonExe)) {
          return reject(new Error(`Python executable not found: ${pythonExe}`));
        }

        if (!fs.existsSync(backendScript)) {
          return reject(new Error(`Backend script not found: ${backendScript}`));
        }

        backendProcess = spawn(pythonExe, [backendScript], {
          cwd: appPath,
          windowsHide: true,
          shell: false
        });
      } else {
        const backendExe = path.join(
          process.resourcesPath,
          "backend",
          "fuel_backend",
          "fuel_backend.exe"
        );

        log("Running in production mode");
        log("Backend exe:", backendExe);

        if (!fs.existsSync(backendExe)) {
          return reject(new Error(`Backend executable not found: ${backendExe}`));
        }

        backendProcess = spawn(backendExe, [], {
          cwd: path.dirname(backendExe),
          windowsHide: true,
          shell: false
        });
      }

      backendProcess.on("spawn", () => {
        log("Backend process spawned successfully.");
      });

      backendProcess.on("error", (error) => {
        logError("Backend process error:", error);
        reject(error);
      });

      backendProcess.on("close", (code, signal) => {
        log("Backend process closed.", "code:", code, "signal:", signal);
        backendProcess = null;
      });

      backendProcess.on("exit", (code, signal) => {
        log("Backend process exited.", "code:", code, "signal:", signal);
      });

      if (backendProcess.stdout) {
        backendProcess.stdout.on("data", (data) => {
          console.log("[backend stdout]", data.toString().trim());
        });
      }

      if (backendProcess.stderr) {
        backendProcess.stderr.on("data", (data) => {
          console.error("[backend stderr]", data.toString().trim());
        });
      }

      waitForBackend(BACKEND_HEALTH_URL, 30000)
        .then(() => resolve())
        .catch((error) => reject(error));
    } catch (error) {
      reject(error);
    }
  });
}

async function loadFrontend(window) {
  log("Loading frontend...");

  if (isDev) {
    const devServerAvailable = await checkUrl(FRONTEND_DEV_URL, 1500);

    if (devServerAvailable) {
      log("Frontend dev server found:", FRONTEND_DEV_URL);
      await window.loadURL(FRONTEND_DEV_URL);
      return;
    }

    log("Frontend dev server not available. Trying build file...");
  }

  log("Checking frontend build file:", FRONTEND_BUILD_FILE);

  if (fs.existsSync(FRONTEND_BUILD_FILE)) {
    await window.loadFile(FRONTEND_BUILD_FILE);
    return;
  }

  throw new Error(
    "Frontend not found. Run 'npm run frontend:build' first, or use 'npm run dev'."
  );
}

function createWindow() {
  log("Creating browser window...");

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1200,
    minHeight: 760,
    autoHideMenuBar: true,
    icon: path.join(__dirname, "favicon.ico"),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      devTools: isDev
    }
  });

  mainWindow.webContents.on("did-finish-load", () => {
    log("Frontend finished loading.");
  });

  mainWindow.webContents.on(
    "did-fail-load",
    (event, errorCode, errorDescription, validatedURL) => {
      logError(
        "Frontend failed to load:",
        "code:", errorCode,
        "description:", errorDescription,
        "url:", validatedURL
      );
    }
  );

  mainWindow.webContents.on("console-message", (event, level, message, line, sourceId) => {
    console.log(`[renderer console] ${message} (${sourceId}:${line})`);
  });

  mainWindow.webContents.on("render-process-gone", (event, details) => {
    logError("Renderer process gone:", details);
  });

  mainWindow.on("closed", () => {
    log("Main window closed.");
    mainWindow = null;
  });

  loadFrontend(mainWindow).catch((error) => {
    logError("Failed to load frontend:", error);

    const html = `
      <html>
        <body style="font-family: Arial, sans-serif; padding: 24px;">
          <h2>Frontend failed to load</h2>
          <p>${String(error.message)}</p>
          <p>Run <b>npm run frontend:build</b> first, or use <b>npm run dev</b>.</p>
        </body>
      </html>
    `;

    mainWindow.loadURL(`data:text/html;charset=UTF-8,${encodeURIComponent(html)}`);
  });
}

process.on("uncaughtException", (error) => {
  logError("Uncaught Exception:", error);
});

process.on("unhandledRejection", (reason) => {
  logError("Unhandled Rejection:", reason);
});

app.whenReady().then(async () => {
  log("App is ready.");
  log("isDev =", isDev);

  try {
    await startBackend();
    createWindow();

    app.on("activate", () => {
      log("App activate event.");

      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  } catch (error) {
    logError("Failed to start application:", error);
    app.quit();
  }
});

app.on("window-all-closed", () => {
  log("All windows closed.");

  if (backendProcess && !backendProcess.killed) {
    log("Killing backend process...");
    backendProcess.kill();
  }

  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  log("Before quit.");

  if (backendProcess && !backendProcess.killed) {
    log("Killing backend process before quit...");
    backendProcess.kill();
  }
});