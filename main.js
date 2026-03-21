const { app, BrowserWindow, ipcMain, Notification, screen } = require('electron')
const path = require('path')

let overlayWin = null
let setupWin = null

function createSetupWindow() {
  setupWin = new BrowserWindow({
    width: 360,
    height: 280,
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
    if (!overlayWin) app.quit()
  })
}

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
    type: 'toolbar',
  })

  overlayWin.setAlwaysOnTop(true, 'screen-saver')

  overlayWin.setIgnoreMouseEvents(true, { forward: true })

  overlayWin.loadFile('overlay.html', {
    query: { seconds: String(totalSeconds) },
  })

  overlayWin.on('closed', () => {
    overlayWin = null
    app.quit()
  })
}

ipcMain.on('start-timer', (_, totalSeconds) => {
  if (setupWin) {
    setupWin.close()
    setupWin = null
  }
  createOverlayWindow(totalSeconds)
})

ipcMain.on('close-overlay', () => {
  if (overlayWin) overlayWin.close()
})

ipcMain.on('move-overlay', (_, { dx, dy }) => {
  if (!overlayWin) return
  const [x, y] = overlayWin.getPosition()
  overlayWin.setPosition(x + dx, y + dy)
})

ipcMain.on('toggle-click-through', (_, enabled) => {
  if (!overlayWin) return
  overlayWin.setIgnoreMouseEvents(enabled, { forward: true })
})

ipcMain.on('timer-done', () => {
  new Notification({
    title: '⏱ Timer Overlay',
    body: 'Le temps est écoulé !',
    urgency: 'critical',
    //sound: ''
  }).show()
})

ipcMain.on('restart-timer', () => {
  if (!setupWin) {
    createSetupWindow()
  }

  if (overlayWin) {
    overlayWin.removeAllListeners('closed')
    overlayWin.close() 
    overlayWin = null
  }
})

app.whenReady().then(() => {
  createSetupWindow()
})

app.on('window-all-closed', () => app.quit())
