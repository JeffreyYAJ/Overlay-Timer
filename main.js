const { app, BrowserWindow, ipcMain, Notification, screen } = require('electron')
const path = require('path')

let overlayWin = null
let setupWin = null

// ── Fenêtre de configuration ──────────────────────────────────────────
function createSetupWindow() {
  setupWin = new BrowserWindow({
    width: 360,
    height: 260,
    resizable: false,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    center: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  })

  setupWin.loadFile('setup.html')

  setupWin.on('closed', () => {
    setupWin = null
    // Si l'overlay n'existe pas non plus → quitter
    if (!overlayWin) app.quit()
  })
}

// ── Fenêtre overlay (minuteur transparent) ────────────────────────────
function createOverlayWindow(totalSeconds) {
  const { width } = screen.getPrimaryDisplay().workAreaSize

  overlayWin = new BrowserWindow({
    width: 240,
    height: 110,
    x: width - 260,
    y: 30,
    frame: false,
    transparent: true,           // fond transparent
    alwaysOnTop: true,           // toujours devant
    skipTaskbar: true,           // pas dans la barre des tâches
    focusable: false,            // ne prend pas le focus
    hasShadow: false,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    // Type 'toolbar' + level 'screen-saver' = overlay max priorité sur Linux/X11
    type: 'toolbar',
  })

  overlayWin.setAlwaysOnTop(true, 'screen-saver')

  // ── Clic-through : la fenêtre ignore tous les événements souris ──────
  overlayWin.setIgnoreMouseEvents(true, { forward: true })
  // Note : forward:true renvoie les events à la renderer pour drag-to-move

  overlayWin.loadFile('overlay.html', {
    query: { seconds: String(totalSeconds) },
  })

  overlayWin.on('closed', () => {
    overlayWin = null
    app.quit()
  })
}

// ── IPC : setup → overlay ─────────────────────────────────────────────
ipcMain.on('start-timer', (_, totalSeconds) => {
  if (setupWin) {
    setupWin.close()
    setupWin = null
  }
  createOverlayWindow(totalSeconds)
})

// Fermer l'overlay depuis le renderer (clic bouton ×)
ipcMain.on('close-overlay', () => {
  if (overlayWin) overlayWin.close()
})

// Déplacer l'overlay (drag manuel, puisque clic-through est actif)
ipcMain.on('move-overlay', (_, { dx, dy }) => {
  if (!overlayWin) return
  const [x, y] = overlayWin.getPosition()
  overlayWin.setPosition(x + dx, y + dy)
})

// Basculer clic-through depuis le renderer
ipcMain.on('toggle-click-through', (_, enabled) => {
  if (!overlayWin) return
  overlayWin.setIgnoreMouseEvents(enabled, { forward: true })
})

// Notification système quand le timer se termine
ipcMain.on('timer-done', () => {
  new Notification({
    title: '⏱ Timer Overlay',
    body: 'Le temps est écoulé !',
    urgency: 'critical',
  }).show()
})

// Relancer : fermer l'overlay et rouvrir la fenêtre de config
ipcMain.on('restart-timer', () => {
  if (overlayWin) {
    overlayWin.destroy()
    overlayWin = null
  }
  createSetupWindow()
})

// ── Init ──────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  createSetupWindow()
})

app.on('window-all-closed', () => app.quit())
