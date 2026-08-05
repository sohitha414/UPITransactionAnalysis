import express from "express";
import path from "path";
import { spawn, execSync } from "child_process";
import { createServer as createViteServer } from "vite";
import httpProxy from "http-proxy";

const app = express();
const PORT = 3000;

app.use(express.json());

// Proxy setup for Python FastAPI and Streamlit
const proxy = httpProxy.createProxyServer({});

proxy.on("error", (err, req, res) => {
  console.error("Proxy error:", err.message);
  if (!res.headersSent) {
    res.status(502).json({ error: "Backend service starting up, please refresh in a moment..." });
  }
});

// Helper to launch Python background services
function startPythonServices() {
  console.log("Checking Python environment & database initialization...");

  try {
    // 1. Seed database if not existing
    execSync("python3 data_pipeline/seed_db.py", { stdio: "inherit" });
  } catch (err) {
    console.warn("Notice: DB seed script step skipped or had warning:", err);
  }

  try {
    // 2. Train initial model if missing
    execSync("python3 ml/train_model.py", { stdio: "inherit" });
  } catch (err) {
    console.warn("Notice: ML model training step skipped or had warning:", err);
  }

  // 3. Start FastAPI server on port 8000
  console.log("Launching FastAPI service on port 8000...");
  const fastApiProc = spawn("python3", ["-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"], {
    stdio: "pipe",
    env: { ...process.env }
  });

  fastApiProc.stdout.on("data", (d) => console.log(`[FastAPI] ${d.toString().trim()}`));
  fastApiProc.stderr.on("data", (d) => console.error(`[FastAPI Error] ${d.toString().trim()}`));

  // 4. Start Streamlit server on port 8501
  console.log("Launching Streamlit service on port 8501...");
  const streamlitProc = spawn(
    "python3",
    [
      "-m", "streamlit", "run", "dashboard/app.py",
      "--server.port=8501",
      "--server.address=127.0.0.1",
      "--server.baseUrlPath=streamlit",
      "--server.headless=true",
      "--theme.base=light"
    ],
    { stdio: "pipe", env: { ...process.env } }
  );

  streamlitProc.stdout.on("data", (d) => console.log(`[Streamlit] ${d.toString().trim()}`));
  streamlitProc.stderr.on("data", (d) => console.error(`[Streamlit Error] ${d.toString().trim()}`));
}

// Proxy /api requests to FastAPI on 8000
app.use("/api", (req, res) => {
  req.url = `/api${req.url}`;
  proxy.web(req, res, { target: "http://127.0.0.1:8000" });
});

// Proxy /streamlit requests to Streamlit on 8501
app.use("/streamlit", (req, res) => {
  proxy.web(req, res, { target: "http://127.0.0.1:8501" });
});

async function main() {
  startPythonServices();

  // Vite development middleware
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`=======================================================`);
    console.log(`🚀 UPI Transaction Analysis Server active on port ${PORT}`);
    console.log(`=======================================================`);
  });
}

main();
