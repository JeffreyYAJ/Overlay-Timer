# ⏱ Timer Overlay — Electron (Linux)

Minuteur transparent always-on-top pour Linux, basé sur **Electron**.

## Installation

```bash
# Pré-requis : Node.js ≥ 18
node --version

# Dans le dossier du projet
npm install

# Lancer
npm start
```

## Structure des fichiers

```
timer-overlay/
├── main.js        ← Processus principal Electron (fenêtres, IPC, notifications)
├── setup.html     ← Boîte de dialogue de configuration
├── overlay.html   ← L'overlay transparent always-on-top
├── package.json
└── README.md
```

## Fonctionnement

1. Au lancement → fenêtre de configuration (choisir durée + presets 1/5/10/25 min)
2. Clic "Démarrer" → overlay transparent apparaît en haut à droite
3. L'overlay reste devant toutes les fenêtres, **ne bloque pas les clics** (clic-through actif par défaut)
4. Notification système à la fin

## Raccourcis

| Action | Raccourci |
|--------|-----------|
| Pause / Reprise | `Espace` ou double-clic sur l'overlay |
| Basculer clic-through | `T` |
| Fermer | `Echap` ou `Q` ou bouton `✕` |
| Déplacer l'overlay | Glisser la zone du haut |

## Flags Electron utilisés

```js
transparent: true          // fond ARGB
alwaysOnTop: true
setAlwaysOnTop('screen-saver')  // niveau max
skipTaskbar: true
focusable: false
setIgnoreMouseEvents(true, { forward: true })  // clic-through + events drag forwarded
type: 'toolbar'            // overlay natif Linux/X11
```

## Compiler en AppImage (optionnel)

```bash
npm install electron-builder --save-dev
npm run build
# → dist/Timer Overlay-1.0.0.AppImage
```

## Notes Wayland

Sur Wayland, `setAlwaysOnTop('screen-saver')` fonctionne sur KWin (KDE) et
partiellement sur Mutter (GNOME). Si l'overlay passe derrière des fenêtres,
forcer X11 : `ELECTRON_OZONE_PLATFORM_HINT=x11 npm start`
